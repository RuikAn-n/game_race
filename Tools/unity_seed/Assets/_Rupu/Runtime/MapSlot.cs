// 布局建筑位：由 入谱/永昌堡 生成场景时创建。
using UnityEngine;

namespace Rupu
{
    /// <summary>布局里的一个建筑位（与年代无关）。换年代时只换它下面的模型。</summary>
    public class MapSlot : MonoBehaviour
    {
        public string id;
        public string kind;
        public string displayName;
        public string eras;
    }
}
