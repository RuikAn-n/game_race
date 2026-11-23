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
            if (player != null && door != null) player.LookAt(door.position + Vector3.up, 2.5f);

            Vector3 start = soldier != null ? soldier.position : Vector3.zero;
            Vector3 target = door != null ? door.position + new Vector3(0.9f, 0f, 0f) : start;
            float t = 0f;
            while (t < 1f)
            {
                t += Time.deltaTime * 0.85f;
                float smooth = Mathf.SmoothStep(0f, 1f, t);
                if (soldier != null) soldier.position = Vector3.Lerp(start, target, smooth);
                yield return null;
            }

            if (door != null) door.rotation = Quaternion.Euler(0f, 0f, 72f);
            if (loot != null) loot.position = loot.position + new Vector3(0.8f, 0.1f, 0f);
            if (director != null)
            {
                director.Tell("街坊", "日军一脚踹开铺门，把箱子拖到街上。没人敢出声。", () =>
                {
                    director.SetEventBlock(false);
                });
            }
            Debug.Log("[Act1] 日军砸门抢劫");
        }
    }
}
