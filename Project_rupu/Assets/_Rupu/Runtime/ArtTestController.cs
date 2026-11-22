// 《入谱》美术测试用双视角控制器（不是正式玩法代码，正式控制器由 A 实现）
//  - 第三人称：WASD 移动，Shift 跑，鼠标转视角，滚轮拉近拉远
//  - 俯视（策略）：Tab 切换；WASD 平移镜头，滚轮缩放，Q/E 旋转
//  - 若角色子物体上有 Animator 且带 float 参数 "Speed"，会自动驱动
using UnityEngine;

namespace Rupu
{
    [RequireComponent(typeof(CharacterController))]
    public class ArtTestController : MonoBehaviour
    {
        public Camera cam;
        public float walkSpeed = 2.0f, runSpeed = 5.0f;
        [Header("第三人称")] public float tpDistance = 4.5f, tpHeight = 1.6f, mouseSens = 3f;
        [Header("俯视")] public float tdHeight = 22f, tdPitch = 60f, tdPanSpeed = 15f;
        [Range(0.5f, 20f)] public float blendSpeed = 6f;

        enum Mode { ThirdPerson, TopDown }
        Mode mode = Mode.ThirdPerson;
        CharacterController cc;
        Animator anim;
        bool animHasSpeed;
        float yaw, pitch = 15f, tdYaw, vy;
        Vector3 tdFocus;

        void Start()
        {
            cc = GetComponent<CharacterController>();
            if (cam == null) cam = Camera.main;
            anim = GetComponentInChildren<Animator>();
            if (anim != null)
                foreach (var p in anim.parameters)
                    if (p.name == "Speed" && p.type == AnimatorControllerParameterType.Float) animHasSpeed = true;
            yaw = transform.eulerAngles.y;
            Cursor.lockState = CursorLockMode.Locked;
        }

#if ENABLE_LEGACY_INPUT_MANAGER
        void Update()
        {
            if (Input.GetKeyDown(KeyCode.Tab))
            {
                mode = mode == Mode.ThirdPerson ? Mode.TopDown : Mode.ThirdPerson;
                tdFocus = transform.position; tdYaw = yaw;
                Cursor.lockState = mode == Mode.ThirdPerson ? CursorLockMode.Locked : CursorLockMode.None;
            }
            if (Input.GetKeyDown(KeyCode.Escape)) Cursor.lockState = CursorLockMode.None;
            if (Input.GetMouseButtonDown(0) && mode == Mode.ThirdPerson) Cursor.lockState = CursorLockMode.Locked;
            // 测试用：F1 民国 / F2 明代 / F3 美术测试场景；T 依次传送到主要地点
            if (Input.GetKeyDown(KeyCode.F1)) LoadIfExists("Map_Yongchang_ROC");
            if (Input.GetKeyDown(KeyCode.F2)) LoadIfExists("Map_Yongchang_MING");
            if (Input.GetKeyDown(KeyCode.F3)) LoadIfExists("ArtTest");
            if (Input.GetKeyDown(KeyCode.T)) TeleportNext();

            var move = new Vector3(Input.GetAxisRaw("Horizontal"), 0, Input.GetAxisRaw("Vertical"));
            move = Vector3.ClampMagnitude(move, 1f);
            float scroll = Input.GetAxis("Mouse ScrollWheel");
            float speed = 0f;

            if (mode == Mode.ThirdPerson)
            {
                yaw += Input.GetAxis("Mouse X") * mouseSens;
                pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * mouseSens, -20f, 70f);
                tpDistance = Mathf.Clamp(tpDistance - scroll * 5f, 1.5f, 12f);

                var dir = Quaternion.Euler(0, yaw, 0) * move;
                speed = (Input.GetKey(KeyCode.LeftShift) ? runSpeed : walkSpeed) * move.magnitude;
                if (dir.sqrMagnitude > 0.001f)
                    transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), 12f * Time.deltaTime);
                vy = cc.isGrounded ? -1f : vy - 9.81f * Time.deltaTime;
                cc.Move((dir * speed + Vector3.up * vy) * Time.deltaTime);

                var pivot = transform.position + Vector3.up * (tpHeight - cc.height * 0.5f * transform.localScale.y);
                var rot = Quaternion.Euler(pitch, yaw, 0);
                Blend(pivot - rot * Vector3.forward * tpDistance, rot);
            }
            else
            {
                if (Input.GetKey(KeyCode.Q)) tdYaw -= 90f * Time.deltaTime;
                if (Input.GetKey(KeyCode.E)) tdYaw += 90f * Time.deltaTime;
                tdHeight = Mathf.Clamp(tdHeight - scroll * tdHeight * 0.8f, 6f, 300f);   // 可拉远到看全图
                tdFocus += Quaternion.Euler(0, tdYaw, 0) * move * tdPanSpeed * Mathf.Max(1f, tdHeight / 22f) * Time.deltaTime;
                var rot = Quaternion.Euler(tdPitch, tdYaw, 0);
                float back = tdHeight / Mathf.Tan(tdPitch * Mathf.Deg2Rad);
                var pos = tdFocus + Vector3.up * tdHeight - Quaternion.Euler(0, tdYaw, 0) * Vector3.forward * back;
                Blend(pos, rot);
            }

            if (animHasSpeed) anim.SetFloat("Speed", speed, 0.1f, Time.deltaTime);
        }
#else
        void Update() { }
        void OnEnable() { Debug.LogWarning("[Rupu] ArtTestController 需要 Player Settings > Active Input Handling 包含 Input Manager (Old) 或 Both。"); }
#endif

        static readonly string[] TeleportIds =
        {
            "spawn_1941", "spawn_1560", "anchor_zuci_door", "anchor_gate_N", "anchor_muster_huanhai",
            "anchor_wengcheng_arena", "anchor_watergate_arena", "anchor_temple_front", "anchor_granary", "anchor_dock",
        };
        int tpIndex = -1;
        string tpLabel = "";

        void TeleportNext()
        {
            for (int k = 0; k < TeleportIds.Length; k++)
            {
                tpIndex = (tpIndex + 1) % TeleportIds.Length;
                var a = MapAnchor.Find(TeleportIds[tpIndex]);
                if (a == null) continue;
                cc.enabled = false;
                transform.position = a.transform.position + Vector3.up * 0.2f + a.transform.forward * 2f;
                cc.enabled = true;
                yaw = a.transform.eulerAngles.y;
                tdFocus = transform.position;
                tpLabel = a.note;
                return;
            }
        }

        static void LoadIfExists(string scene)
        {
            if (Application.CanStreamedLevelBeLoaded(scene)) UnityEngine.SceneManagement.SceneManager.LoadScene(scene);
        }

        void Blend(Vector3 pos, Quaternion rot)
        {
            float t = 1f - Mathf.Exp(-blendSpeed * Time.deltaTime);
            cam.transform.position = Vector3.Lerp(cam.transform.position, pos, t);
            cam.transform.rotation = Quaternion.Slerp(cam.transform.rotation, rot, t);
        }

        void OnGUI()
        {
            GUI.Label(new Rect(12, 10, 900, 22), mode == Mode.ThirdPerson
                ? "第三人称 | WASD 移动  Shift 跑  鼠标视角  滚轮距离  Tab 切俯视  Esc 释放鼠标"
                : "俯视/策略 | WASD 平移  Q/E 旋转  滚轮缩放  Tab 回第三人称");
            GUI.Label(new Rect(12, 50, 900, 22), "F1 民国场景  F2 明代场景  F3 美术测试  T 传送到下一个地点" + (tpLabel != "" ? $"（{tpLabel}）" : ""));
            GUI.Label(new Rect(12, 30, 600, 22), $"FPS {1f / Mathf.Max(Time.smoothDeltaTime, 1e-5f):0}  |  {SystemInfo.graphicsDeviceType}  |  {SystemInfo.graphicsDeviceName}");
        }
    }
}
