using System.Collections;
using UnityEngine;

namespace Rupu
{
    public class Act1DoorBreak : MonoBehaviour
    {
        public Act1Player player;
        public Act1Director director;
        public Transform soldier;
        public Transform door;
        public Transform loot;
        public Transform triggerPoint;
        public float triggerZ = 58f;
        public float triggerRadius = 3f;
        // 真模型的两扇铺门（枢轴在门轴）：被踹开时各自绕 Y 转开 swingAngles 度；为空时沿用 door 整块倒下
        public Transform[] doorLeaves = new Transform[0];
        public float[] swingAngles = { -100f, 105f };
        // 士兵走到哪里踹门（door 为空时用）；旁观街坊：事件中躲闪
        public Vector3 kickPoint;
        public Act1ClanActor[] bystanders = new Act1ClanActor[0];
        private bool done;

        private void Update()
        {
            if (done || player == null) return;
            if (director != null && director.BlocksMovement) return;
            if (triggerPoint != null)
            {
                if (Vector3.Distance(player.transform.position, triggerPoint.position) > triggerRadius) return;
            }
            else if (player.transform.position.z < triggerZ) return;

            done = true;
            StartCoroutine(BreakDoor());
        }

        private IEnumerator BreakDoor()
        {
            if (director != null) director.SetEventBlock(true);
            Vector3 focus = door != null ? door.position : kickPoint;
            if (player != null) player.LookAt(focus + Vector3.up, 2.5f);
            foreach (Act1ClanActor b in bystanders) if (b != null) b.ambient = "CowerLoop";

            Vector3 start = soldier != null ? soldier.position : Vector3.zero;
            Vector3 target = door != null ? door.position + new Vector3(0.9f, 0f, 0f) : kickPoint;
            float t = 0f;
            while (t < 1f)
            {
                t += Time.deltaTime * 0.85f;
                float smooth = Mathf.SmoothStep(0f, 1f, t);
                if (soldier != null) soldier.position = Vector3.Lerp(start, target, smooth);
                yield return null;
            }

            Act1ClanActor kicker = soldier != null ? soldier.GetComponent<Act1ClanActor>() : null;
            if (kicker != null) { kicker.PlayFor("Push", 1.2f); yield return new WaitForSeconds(0.45f); }
            if (door != null) door.rotation = Quaternion.Euler(0f, 0f, 72f);
            if (doorLeaves != null && doorLeaves.Length > 0) StartCoroutine(SwingLeaves());
            if (loot != null) StartCoroutine(DragLoot());
            if (director != null)
            {
                director.Tell("街坊", "日军一脚踹开铺门，把箱子拖到街上。没人敢出声。", () =>
                {
                    director.SetEventBlock(false);
                });
            }
            Debug.Log("[Act1] 日军砸门抢劫");
        }

        private IEnumerator SwingLeaves()
        {
            Quaternion[] from = new Quaternion[doorLeaves.Length];
            for (int i = 0; i < doorLeaves.Length; i++) if (doorLeaves[i] != null) from[i] = doorLeaves[i].localRotation;
            float t = 0f;
            while (t < 1f)
            {
                t = Mathf.Min(1f, t + Time.deltaTime * 3.5f);
                float e = 1f - (1f - t) * (1f - t) * (1f - t);       // 踹开：先快后慢
                for (int i = 0; i < doorLeaves.Length; i++)
                {
                    if (doorLeaves[i] == null) continue;
                    float a = swingAngles != null && swingAngles.Length > 0 ? swingAngles[i % swingAngles.Length] : 100f;
                    doorLeaves[i].localRotation = from[i] * Quaternion.Euler(0f, a * e, 0f);
                }
                yield return null;
            }
        }

        private IEnumerator DragLoot()
        {   // 把箱子从铺里拖到街上
            Vector3 a = loot.position;
            Vector3 b = a + (soldier != null ? (soldier.position - a).normalized * 1.6f : new Vector3(0.8f, 0f, 0f));
            b.y = a.y;
            float t = 0f;
            while (t < 1f)
            {
                t += Time.deltaTime * 0.6f;
                loot.position = Vector3.Lerp(a, b, Mathf.SmoothStep(0f, 1f, t));
                yield return null;
            }
            foreach (Act1ClanActor by in bystanders) if (by != null) by.ambient = "WatchLoop";
        }
    }
}
