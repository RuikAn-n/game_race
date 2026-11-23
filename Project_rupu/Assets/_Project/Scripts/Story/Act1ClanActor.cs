using System.Collections.Generic;
using UnityEngine;

namespace Rupu
{
    /// <summary>
    /// 第一幕里的 NPC 演员（挂在人物模型根上）。每帧按优先级决定播什么：
    ///   1. 动作（Hold / PlayFor）：拔刀、推搡、倒地、招手、争吵……
    ///   2. 走路：被剧情脚本直接改 position 移动时，按位移速度驱动 Speed，并朝移动方向转身；
    ///   3. 说话：对白标题在 speakerTitles 里时播 TalkLoop（Act1Director 每换一句就调用 Act1ClanActor.Speak）；
    ///   4. 常态：ambient（WatchLoop 围观 / AttentionLoop 站定 / CowerLoop 躲闪），为空时就是待机。
    /// 玩家走近 faceRadius 内会转身面向玩家（facePlayer = false 的不转，比如背对人群的日本兵）。
    /// 动作名 = AC_Humanoid_Locomotion 里的状态名（见 RupuCharacters.Gestures）。
    /// </summary>
    public class Act1ClanActor : MonoBehaviour
    {
        public Transform player;
        public string[] speakerTitles = new string[0];
        public string ambient = "";
        public bool facePlayer = true;
        public float faceRadius = 4.5f;
        public float turnSpeed = 240f;

        private static readonly List<Act1ClanActor> All = new List<Act1ClanActor>();
        private static readonly int SpeedId = Animator.StringToHash("Speed");
        private const string Locomotion = "Locomotion";

        private Animator animator;
        private Quaternion homeRotation;
        private Vector3 lastPosition;
        private float speed;
        private bool talking;
        private string action = "";
        private float actionUntil;
        private string playing = "";
        private Transform faceTarget;

        /// <summary>换了一句对白：标题匹配的演员说话，其余停下。title 为空 = 对白结束。</summary>
        public static void Speak(string title)
        {
            foreach (Act1ClanActor a in All)
            {
                bool match = false;
                if (!string.IsNullOrEmpty(title))
                {
                    foreach (string s in a.speakerTitles)
                    {
                        if (!string.IsNullOrEmpty(s) && title.StartsWith(s)) { match = true; break; }
                    }
                }
                a.talking = match;
            }
        }

        /// <summary>给没有 Act1ClanActor 的 Animator（玩家王砚）直接切动作；state 为空回到走跑。</summary>
        public static void PlayOn(Animator anim, string state, float fade = 0.25f)
        {
            if (anim == null || anim.runtimeAnimatorController == null) return;
            string s = string.IsNullOrEmpty(state) ? Locomotion : state;
            int hash = Animator.StringToHash(s);
            if (anim.HasState(0, hash)) anim.CrossFadeInFixedTime(hash, fade, 0);
        }

        /// <summary>一直保持某个动作（倒地、拔刀后指人、争吵），直到 Release。</summary>
        public void Hold(string state)
        {
            action = state ?? "";
            actionUntil = float.MaxValue;
        }

        /// <summary>播一段动作，seconds 秒后回到常态（招手、推搡）。</summary>
        public void PlayFor(string state, float seconds)
        {
            action = state ?? "";
            actionUntil = Time.time + seconds;
        }

        public void Release()
        {
            action = "";
        }

        /// <summary>转身看向某处（为空 = 恢复看玩家/原朝向）。</summary>
        public void LookAt(Transform target)
        {
            faceTarget = target;
        }

        private void OnEnable()
        {
            if (!All.Contains(this)) All.Add(this);
        }

        private void OnDisable()
        {
            All.Remove(this);
        }

        private void Start()
        {
            animator = GetComponentInChildren<Animator>();
            homeRotation = transform.rotation;
            lastPosition = transform.position;
            if (player == null)
            {
                Act1Player p = FindObjectOfType<Act1Player>();
                if (p != null) player = p.transform;
            }
        }

        private void LateUpdate()
        {
            float dt = Mathf.Max(Time.deltaTime, 1e-4f);
            Vector3 delta = transform.position - lastPosition;
            delta.y = 0f;
            lastPosition = transform.position;
            // 剧情里的轻微抖动（争吵时 ±4cm）不算走路：低于 0.3 m/s 视为站着
            float raw = delta.magnitude / dt;
            speed = Mathf.Lerp(speed, raw > 0.3f ? raw : 0f, 1f - Mathf.Exp(-10f * dt));
            bool moving = speed > 0.3f;
            if (animator != null && animator.runtimeAnimatorController != null) animator.SetFloat(SpeedId, speed);

            if (action.Length > 0 && Time.time > actionUntil) action = "";
            string want = action.Length > 0 ? action : moving ? Locomotion : talking ? "TalkLoop" : ambient.Length > 0 ? ambient : Locomotion;
            if (want != playing)
            {
                playing = want;
                PlayOn(animator, want);
            }

            Quaternion rot = homeRotation;
            if (moving && action.Length == 0 && delta.sqrMagnitude > 1e-6f)
            {
                rot = Quaternion.LookRotation(delta.normalized, Vector3.up);
                homeRotation = rot;     // 走到哪就以到达时的朝向为新的“原朝向”
            }
            else
            {
                Transform look = faceTarget != null ? faceTarget : facePlayer ? player : null;
                if (look != null)
                {
                    Vector3 to = look.position - transform.position;
                    to.y = 0f;
                    bool near = faceTarget != null || to.sqrMagnitude < faceRadius * faceRadius;
                    if (near && to.sqrMagnitude > 0.01f) rot = Quaternion.LookRotation(to.normalized, Vector3.up);
                }
            }
            transform.rotation = Quaternion.RotateTowards(transform.rotation, rot, turnSpeed * dt);
        }
    }
}
