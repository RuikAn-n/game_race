using UnityEngine;

namespace Rupu
{
    /// <summary>
    /// 第一幕祠堂里的族亲/三派演员（挂在人物模型根上）：
    /// - 玩家走近（faceRadius 内）时慢慢转身面向玩家，走开后转回原朝向；
    /// - 被剧情脚本直接改 position 移动时（族老带路、族长上前、三派聚拢），
    ///   按位移速度驱动 Animator 的 Speed 参数并朝移动方向转身，播走路而不是滑行。
    /// </summary>
    public class Act1ClanActor : MonoBehaviour
    {
        public Transform player;
        public float faceRadius = 4.5f;
        public float turnSpeed = 240f;

        private Animator animator;
        private Quaternion homeRotation;
        private Vector3 lastPosition;
        private float speed;
        private static readonly int SpeedId = Animator.StringToHash("Speed");

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
            // 剧情里的抖动（争吵时 ±4cm）不算走路：低于 0.3 m/s 视为站着
            float raw = delta.magnitude / dt;
            speed = Mathf.Lerp(speed, raw > 0.3f ? raw : 0f, 1f - Mathf.Exp(-10f * dt));
            if (animator != null && animator.runtimeAnimatorController != null) animator.SetFloat(SpeedId, speed);

            Quaternion want = homeRotation;
            if (speed > 0.3f && delta.sqrMagnitude > 1e-6f)
            {
                want = Quaternion.LookRotation(delta.normalized, Vector3.up);
                homeRotation = want;     // 走到哪就以到达时的朝向为新的“原朝向”
            }
            else if (player != null)
            {
                Vector3 to = player.position - transform.position;
                to.y = 0f;
                if (to.sqrMagnitude < faceRadius * faceRadius && to.sqrMagnitude > 0.01f)
                    want = Quaternion.LookRotation(to.normalized, Vector3.up);
            }
            transform.rotation = Quaternion.RotateTowards(transform.rotation, want, turnSpeed * dt);
        }
    }
}
