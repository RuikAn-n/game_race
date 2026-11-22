// 地图挂点：由 入谱/永昌堡 生成场景时创建。A 的玩法代码按 id 查找（城门、水门、炮位、Boss 场地、出生点……）。
using UnityEngine;

namespace Rupu
{
    public class MapAnchor : MonoBehaviour
    {
        public string id;
        [TextArea] public string note;

        public static MapAnchor Find(string id)
        {
            foreach (var a in FindObjectsOfType<MapAnchor>())
                if (a.id == id) return a;
            return null;
        }

        void OnDrawGizmos()
        {
            Gizmos.color = new Color(0.77f, 0.33f, 0.18f);
            Gizmos.DrawWireSphere(transform.position + Vector3.up * 0.5f, 0.5f);
            Gizmos.DrawLine(transform.position + Vector3.up * 0.5f, transform.position + Vector3.up * 0.5f + transform.forward * 1.5f);
        }
    }
}
