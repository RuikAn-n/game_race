using System.Collections;
using UnityEngine;

namespace Rupu
{
    public class Act1StreetEvent : MonoBehaviour
    {
        public Act1Director director;
        public Act1Player player;
        public Transform officer;
        public Transform bully;
        public Transform vendor;
        public GameObject sword;
        public GameObject basket;
        public Transform triggerPoint;

        public float triggerZ = 41f;
        public float triggerRadius = 3f;
        private bool done;

        private void Update()
        {
            if (done || director == null || player == null) return;
            if (director.stage != Act1Director.Stage.Street) return;
            if (director.BlocksMovement) return;
            if (triggerPoint != null)
            {
                if (Vector3.Distance(player.transform.position, triggerPoint.position) > triggerRadius) return;
            }
            else if (player.transform.position.z < triggerZ) return;

            done = true;
            StartCoroutine(PlayEvent());
        }

        private IEnumerator PlayEvent()
        {
            director.SetEventBlock(true);
            if (player != null)
            {
                Vector3 lookTarget = vendor != null ? vendor.position + Vector3.up * 1.2f : transform.position + Vector3.up;
                player.LookAt(lookTarget, 4f);
            }
            if (sword != null) sword.SetActive(true);

            Vector3 officerStart = officer != null ? officer.position : Vector3.zero;
            Vector3 bullyStart = bully != null ? bully.position : Vector3.zero;
            Vector3 vendorPos = vendor != null ? vendor.position : new Vector3(-5f, 1f, 43f);

            float t = 0f;
            while (t < 1f)
            {
                t += Time.deltaTime * 1.1f;
                float smooth = Mathf.SmoothStep(0f, 1f, t);
                if (officer != null) officer.position = Vector3.Lerp(officerStart, new Vector3(0f, 1f, 40.5f), smooth);
                if (bully != null) bully.position = Vector3.Lerp(bullyStart, vendorPos + new Vector3(0.6f, 0f, 0.3f), smooth);
                if (vendor != null) vendor.rotation = Quaternion.Euler(0f, 0f, Mathf.Lerp(0f, 18f, smooth));
                if (basket != null) basket.transform.position = Vector3.Lerp(basket.transform.position, new Vector3(vendorPos.x - 0.5f, 0.2f, vendorPos.z + 0.7f), smooth);
                yield return null;
            }

            director.Tell("日本兵", "“让开！你的，什么的干活？”");
            director.Tell("小贩", "“太君，太君……饶命，饶命……”");
            director.Tell("日本军官", "“站住。你去哪里？”");
            director.Tell("王砚", "“我……我是王家的人，回来看看。”");
            director.Tell("日本军官", "“走。别多事。”", () =>
            {
                if (sword != null) sword.SetActive(false);
                director.SetEventBlock(false);
                Debug.Log("[Act1] 日军盘问结束，放行");
            });
        }
    }
}
