using UnityEngine;

namespace Rupu
{
    public class Act1Fire : MonoBehaviour
    {
        public float radius = 3f;
        public float height = 5f;
        // ROC 场景改用 PF_VFX_Fire / PF_VFX_FireSmoke（URP 粒子材质），这里只保留火光和哭喊声
        public bool buildFlames = true;

        private Light fireLight;
        private AudioSource source;
        private float nextCry;

        private void Start()
        {
            fireLight = gameObject.AddComponent<Light>();
            fireLight.type = LightType.Point;
            fireLight.color = new Color(1f, 0.42f, 0.12f);
            fireLight.range = 16f;
            fireLight.intensity = 2.2f;

            source = gameObject.AddComponent<AudioSource>();
            source.playOnAwake = false;
            source.spatialBlend = 1f;
            source.rolloffMode = AudioRolloffMode.Linear;
            source.minDistance = 4f;
            source.maxDistance = 24f;
            source.volume = 0.55f;

            if (buildFlames) BuildFlames();
            nextCry = Time.time + 1f;
        }

        private void Update()
        {
            if (fireLight != null)
            {
                fireLight.intensity = 1.8f + Mathf.PerlinNoise(Time.time * 5f, 0.3f) * 1.6f;
            }

            Act1Director director = FindObjectOfType<Act1Director>();
            if (director != null && director.BlocksMovement)
            {
                if (source.isPlaying) source.Pause();
                return;
            }

            if (source != null && source.isPlaying == false && source.time > 0f)
            {
                source.UnPause();
            }

            if (Time.time >= nextCry)
            {
                nextCry = Time.time + Random.Range(4f, 7f);
                AudioClip clip = Resources.Load<AudioClip>(Random.value > 0.45f ? "Act1Audio/scream" : "Act1Audio/cry");
                if (clip != null) source.PlayOneShot(clip, 0.8f);
            }
        }

        private void BuildFlames()
        {
            GameObject flames = new GameObject("Flames");
            flames.transform.SetParent(transform, false);
            flames.transform.localPosition = Vector3.zero;

            ParticleSystem ps = flames.AddComponent<ParticleSystem>();
            ParticleSystem.MainModule main = ps.main;
            main.duration = 2f;
            main.loop = true;
            main.startLifetime = 1.2f;
            main.startSpeed = 1.4f;
            main.startSize = 0.9f;
            main.maxParticles = 180;
            main.startColor = new Color(1f, 0.32f, 0.06f, 0.85f);
            main.gravityModifier = -0.08f;

            ParticleSystem.EmissionModule emission = ps.emission;
            emission.rateOverTime = 90f;

            ParticleSystem.ShapeModule shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 18f;
            shape.radius = radius;

            ParticleSystem.ColorOverLifetimeModule color = ps.colorOverLifetime;
            color.enabled = true;
            Gradient gradient = new Gradient();
            gradient.SetKeys(
                new[] { new GradientColorKey(new Color(1f, 0.75f, 0.22f), 0f), new GradientColorKey(new Color(0.7f, 0.08f, 0.02f), 1f) },
                new[] { new GradientAlphaKey(0.9f, 0f), new GradientAlphaKey(0f, 1f) });
            color.color = gradient;

            ParticleSystemRenderer renderer = flames.GetComponent<ParticleSystemRenderer>();
            Shader shader = Shader.Find("Particles/Standard Unlit");
            if (shader != null) renderer.material = new Material(shader);
        }
    }
}
