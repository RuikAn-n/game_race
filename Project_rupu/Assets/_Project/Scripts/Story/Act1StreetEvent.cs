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
        // 军官走到哪里拦住王砚（灰盒默认带 y=1 的胶囊中心；真人模型原点在脚底，生成器会设成贴地的点）
        public Vector3 officerStop = new Vector3(0f, 1f, 40.5f);
        // 围观的街坊：事件开始时躲闪（CowerLoop），放行后恢复围观
        public Act1ClanActor[] bystanders = new Act1ClanActor[0];
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
            Act1ClanActor officerActor = officer != null ? officer.GetComponent<Act1ClanActor>() : null;
            Act1ClanActor bullyActor = bully != null ? bully.GetComponent<Act1ClanActor>() : null;
            Act1ClanActor vendorActor = vendor != null ? vendor.GetComponent<Act1ClanActor>() : null;
            foreach (Act1ClanActor b in bystanders) if (b != null) b.ambient = "CowerLoop";
            // 胶囊占位没有动画：刀直接出现；真人模型等拔刀动作把手带到刀柄再亮刀
            if (sword != null && officerActor == null) sword.SetActive(true);

            Vector3 officerStart = officer != null ? officer.position : Vector3.zero;
            Vector3 bullyStart = bully != null ? bully.position : Vector3.zero;
            Vector3 vendorPos = vendor != null ? vendor.position : new Vector3(-5f, 1f, 43f);
            Vector3 basketStart = basket != null ? basket.transform.position : Vector3.zero;
            Vector3 basketEnd = new Vector3(vendorPos.x - 0.5f, vendorActor != null ? 0f : 0.2f, vendorPos.z + 0.7f);

            float t = 0f;
            bool pushed = false;
            while (t < 1f)
            {
                t += Time.deltaTime * 1.1f;
                float smooth = Mathf.SmoothStep(0f, 1f, t);
                if (officer != null) officer.position = Vector3.Lerp(officerStart, officerStop, smooth);
                if (bully != null) bully.position = Vector3.Lerp(bullyStart, vendorPos + new Vector3(0.6f, 0f, 0.3f), smooth);
                if (!pushed && t > 0.75f)
                {   // 日本兵冲到跟前一推，小贩倒地
                    pushed = true;
                    if (bullyActor != null) { bullyActor.LookAt(vendor); bullyActor.PlayFor("Push", 1.3f); }
                    if (vendorActor != null) { vendorActor.LookAt(bully); vendorActor.Hold("Fall"); }
                }
                if (vendor != null && vendorActor == null) vendor.rotation = Quaternion.Euler(0f, 0f, Mathf.Lerp(0f, 18f, smooth));
                if (basket != null) basket.transform.position = Vector3.Lerp(basketStart, basketEnd, smooth);
                yield return null;
            }

            if (officerActor != null)
            {   // 军官拔刀指着王砚盘问
                officerActor.LookAt(player != null ? player.transform : null);
                officerActor.Hold("DrawSword");
                yield return new WaitForSeconds(0.55f);
                if (sword != null) sword.SetActive(true);
            }

            director.Tell("日本兵", "“让开！你的，什么的干活？”");
            director.Tell("小贩", "“太君，太君……饶命，饶命……”");
            director.Tell("日本军官", "“站住。你去哪里？”");
            director.Tell("王砚", "“我……我是王家的人，回来看看。”");
            director.Tell("日本军官", "“走。别多事。”", () =>
            {
                if (sword != null) sword.SetActive(false);
                if (officerActor != null) { officerActor.Release(); officerActor.LookAt(null); officerActor.ambient = "AttentionLoop"; }
                foreach (Act1ClanActor b in bystanders) if (b != null) b.ambient = "WatchLoop";
                director.SetEventBlock(false);
                Debug.Log("[Act1] 日军盘问结束，放行");
            });
        }
    }
}
