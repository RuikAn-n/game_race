using UnityEngine;

namespace Rupu
{
    public class Act1Interactable : MonoBehaviour
    {
        public string id;
        public string label = "互动";
        public string prompt = "按住 E";
        public float radius = 2.8f;
        public float holdDuration = 1.6f;
        public Act1Player player;
        public Act1Director director;

        private float progress;
        private bool inRange;
        private bool consumed;
        private GUIStyle labelStyle;
        private GUIStyle hintStyle;
        private Font font;

        private void Start()
        {
            if (player == null) player = FindObjectOfType<Act1Player>();
            if (director == null) director = FindObjectOfType<Act1Director>();
        }

        private void Update()
        {
            if (consumed || player == null || director == null) return;
            if (director.BlocksMovement) { progress = 0f; return; }

            inRange = Vector3.Distance(player.transform.position, transform.position) <= radius;
            if (!inRange)
            {
                progress = 0f;
                return;
            }

            if (Input.GetKey(KeyCode.E))
            {
                progress += Time.deltaTime;
                if (progress >= holdDuration)
                {
                    consumed = true;
                    progress = 0f;
                    director.CompleteInteraction(id);
                }
            }
            else
            {
                progress = Mathf.Max(0f, progress - Time.deltaTime * 2f);
            }
        }

        private void OnGUI()
        {
            if (consumed || director == null || director.BlocksMovement) return;
            if (!inRange) return;

            EnsureStyles();
            Rect panel = new Rect(Screen.width / 2f - 190f, Screen.height - 132f, 380f, 76f);
            GUI.color = new Color(0.04f, 0.03f, 0.02f, 0.82f);
            GUI.DrawTexture(panel, Texture2D.whiteTexture);
            GUI.color = Color.white;

            GUI.Label(new Rect(panel.x + 12f, panel.y + 8f, 356f, 24f), label, labelStyle);
            GUI.Label(new Rect(panel.x + 12f, panel.y + 34f, 356f, 22f), prompt, hintStyle);

            float fill = holdDuration > 0f ? Mathf.Clamp01(progress / holdDuration) : 0f;
            GUI.color = new Color(0.85f, 0.68f, 0.28f);
            GUI.DrawTexture(new Rect(panel.x + 12f, panel.y + 62f, 356f * fill, 5f), Texture2D.whiteTexture);
            GUI.color = Color.white;
        }

        private void EnsureStyles()
        {
            if (labelStyle != null) return;

            if (font == null) font = Font.CreateDynamicFontFromOSFont("Microsoft YaHei", 18);
            labelStyle = new GUIStyle(GUI.skin.label);
            labelStyle.font = font;
            labelStyle.fontSize = 18;
            labelStyle.fontStyle = FontStyle.Bold;
            labelStyle.normal.textColor = new Color(0.96f, 0.9f, 0.76f);

            hintStyle = new GUIStyle(GUI.skin.label);
            hintStyle.font = font;
            hintStyle.fontSize = 15;
            hintStyle.normal.textColor = new Color(0.82f, 0.78f, 0.68f);
        }
    }
}
