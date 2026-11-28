// 《入谱》动画事件接收器：挂在有 Animator 的物体上。Data/anim_events.json 里的每个事件名都有一个同名方法，
// 统一转成 OnEvent(事件名)，玩法脚本订阅它即可（不用每个脚本都写一堆同名方法，也避免「AnimationEvent 没有接收者」报错）。
using System;
using UnityEngine;

namespace Rupu
{
    [DisallowMultipleComponent]
    public class RupuAnimEventRelay : MonoBehaviour
    {
        public event Action<string> OnEvent;
        [Tooltip("在控制台打印收到的事件（调试用）")] public bool log;

        void Raise(string n)
        {
            if (log) Debug.Log($"[AnimEvent] {name}: {n}", this);
            OnEvent?.Invoke(n);
        }

        // 约定名（CLAUDE.md）
        public void AttackHit() => Raise(nameof(AttackHit));
        public void PhaseChange() => Raise(nameof(PhaseChange));
        public void Stagger() => Raise(nameof(Stagger));
        public void Death() => Raise(nameof(Death));
        public void Footstep() => Raise(nameof(Footstep));
        // 第二、三幕建议名
        public void Parry() => Raise(nameof(Parry));
        public void Execute() => Raise(nameof(Execute));
        public void CannonFire() => Raise(nameof(CannonFire));
        public void Ignite() => Raise(nameof(Ignite));
        public void DrumHit() => Raise(nameof(DrumHit));
        public void Splash() => Raise(nameof(Splash));
        public void Plant() => Raise(nameof(Plant));
        public void Lever() => Raise(nameof(Lever));
        public void Grab() => Raise(nameof(Grab));
        public void Give() => Raise(nameof(Give));
        public void Accuse() => Raise(nameof(Accuse));
        public void Receive() => Raise(nameof(Receive));
        public void PryEffort() => Raise(nameof(PryEffort));
        public void BeamFall() => Raise(nameof(BeamFall));
        public void Sleeve() => Raise(nameof(Sleeve));
    }
}
