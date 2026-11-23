using UnityEngine;

namespace Rupu
{
    public class Act1Plane : MonoBehaviour
    {
        public Vector3 center = new Vector3(0f, 20f, 50f);
        public float radius = 30f;
        public float height = 20f;
        public float speed = 0.09f;
        public float phase;
        public float smoothTime = 0.85f;
        // 模型机头朝向修正：旧灰盒方块飞机沿 X 摆放用 90；PROP_JapanesePlane 机头朝 +Z，生成器设 0
        public float modelYawOffset = 90f;

        // 螺旋桨绕机身轴转（世界空间），不依赖 FBX 子物体的本地轴向
        private Vector3 spinAxis() => Quaternion.Euler(0f, -modelYawOffset, 0f) * transform.forward;

        private float angle;
        private Rigidbody body;
        private Vector3 velocity;
        private Transform propeller;
        private AudioSource engineSource;
        private GUIStyle labelStyle;
        private Font font;

        private void Start()
        {
            angle = phase;
            body = GetComponent<Rigidbody>();
            if (body == null) body = gameObject.AddComponent<Rigidbody>();
            body.isKinematic = true;
            body.useGravity = false;
            body.interpolation = RigidbodyInterpolation.Interpolate;
            body.position = OrbitPoint(angle);
            body.rotation = Quaternion.LookRotation(Tangent(angle)) * Quaternion.Euler(0f, modelYawOffset, 0f);
            propeller = transform.Find("Propeller");

            BuildEngineAudio();
        }

        private void Update()
        {
            Act1Director director = FindObjectOfType<Act1Director>();
            if (engineSource != null)
            {
                if (director != null && director.BlocksMovement)
                {
                    if (engineSource.isPlaying) engineSource.Pause();
                }
                else if (!engineSource.isPlaying && engineSource.time > 0f)
                {
                    engineSource.UnPause();
                }
            }

            angle += speed * Time.deltaTime;
            Vector3 target = OrbitPoint(angle);
            Vector3 next = Vector3.SmoothDamp(body.position, target, ref velocity, smoothTime);
            Vector3 direction = target - body.position;
            if (direction.sqrMagnitude > 0.01f)
            {
                Quaternion desired = Quaternion.LookRotation(direction.normalized, Vector3.up) * Quaternion.Euler(0f, modelYawOffset, 0f);
                float bank = Mathf.Clamp(Vector3.SignedAngle(transform.forward, direction, Vector3.up) * 0.35f, -18f, 18f);
                desired *= Quaternion.Euler(0f, 0f, -bank);
                body.MoveRotation(Quaternion.Slerp(body.rotation, desired, Time.deltaTime * 1.6f));
            }
            body.MovePosition(next);

            if (propeller != null) propeller.Rotate(spinAxis(), 1800f * Time.deltaTime, Space.World);
        }

        private Vector3 OrbitPoint(float a)
        {
            return new Vector3(center.x + Mathf.Cos(a) * radius, height, center.z + Mathf.Sin(a) * radius);
        }

        private Vector3 Tangent(float a)
        {
            return new Vector3(-Mathf.Sin(a), 0f, Mathf.Cos(a));
        }

        private void BuildEngineAudio()
        {
            AudioSource source = gameObject.AddComponent<AudioSource>();
            source.playOnAwake = false;
            source.loop = true;
            source.spatialBlend = 0f;
            source.volume = 0.055f;

            int sampleRate = 22050;
            int length = sampleRate * 2;
            float[] samples = new float[length];
            for (int i = 0; i < length; i++)
            {
                float t = (float)i / sampleRate;
                samples[i] = Mathf.Sin(t * 2f * Mathf.PI * 58f) * 0.16f + Random.Range(-0.035f, 0.035f);
            }

            AudioClip clip = AudioClip.Create("PlaneEngine", length, 1, sampleRate, false);
            clip.SetData(samples, 0);
            source.clip = clip;
            source.Play();
            engineSource = source;
        }

        private void OnGUI()
        {
            Camera camera = Camera.main;
            if (camera == null) return;

            Vector3 screen = camera.WorldToScreenPoint(transform.position);
            if (screen.z <= 0f) return;
            if (screen.x < 0f || screen.x > Screen.width || screen.y < 0f || screen.y > Screen.height) return;

            if (labelStyle == null)
            {
                font = Font.CreateDynamicFontFromOSFont("Microsoft YaHei", 16);
                labelStyle = new GUIStyle(GUI.skin.label);
                labelStyle.font = font;
                labelStyle.fontSize = 16;
                labelStyle.fontStyle = FontStyle.Bold;
                labelStyle.alignment = TextAnchor.MiddleCenter;
                labelStyle.normal.textColor = new Color(0.9f, 0.18f, 0.12f);
            }

            GUI.Label(new Rect(screen.x - 34f, Screen.height - screen.y - 24f, 68f, 22f), "日机", labelStyle);
        }
    }
}
