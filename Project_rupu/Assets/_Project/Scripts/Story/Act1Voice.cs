using UnityEngine;

namespace Rupu
{
    public class Act1Voice : MonoBehaviour
    {
        private AudioSource source;

        private void Awake()
        {
            source = gameObject.AddComponent<AudioSource>();
            source.playOnAwake = false;
            source.spatialBlend = 0f;
            source.volume = 0.9f;
        }

        public bool IsSpeaking => source != null && source.isPlaying;

        public void PlayFor(string title, string body)
        {
            string key = null;
            if (title == "交谱派族老") key = body != null && body.Contains("上海") ? "jiao2" : "jiao";
            else if (title == "烧谱派青年") key = body != null && body.Contains("断了根") ? "shao2" : "shao";
            else if (title == "藏谱派妇人") key = body != null && body.Contains("查清") ? "cang2" : "cang";
            else if (title == "族中冷遇") key = "cold";
            else if (title == "族中亲善") key = "kind";
            else if (title == "族老")
            {
                if (body != null && body.Contains("回来得不是时候")) key = "elder_arrival";
                else if (body != null && body.Contains("吵了一年")) key = "elder_rumor";
                else if (body != null && body.Contains("跟我来")) key = "elder_lead";
                else if (body != null && body.Contains("别听他们吵")) key = "elder_incense";
                else if (body != null && body.Contains("父亲的位置")) key = "elder_memorial";
                else if (body != null && body.Contains("谱在，人就在")) key = "elder_keep";
                else if (body != null && body.Contains("孩子刚回来")) key = "elder_protect";
                else if (body != null && body.Contains("容我们商量")) key = "elder_plead";
                else key = "elder";
            }
            else if (title == "王秉之")
            {
                if (body != null && body.Contains("我老了")) key = "leader_weak";
                else if (body != null && body.Contains("烧了祠堂")) key = "leader_burn";
                else if (body != null && body.Contains("谱是王氏的根")) key = "leader_response";
                else if (body != null && body.Contains("谱是王氏的")) key = "leader_refuse";
                else if (body != null && body.Contains("不必商量")) key = "leader_firm";
                else key = "leader";
            }
            else if (title == "日本兵") key = "insult";
            else if (title == "小贩") key = "cry";
            else if (title == "日本军官")
            {
                if (body != null && body.Contains("你就是王砚")) key = "officer_identify";
                else if (body != null && body.Contains("王氏族约")) key = "officer_threat2";
                else if (body != null && body.Contains("更懂它")) key = "officer_culture";
                else if (body != null && body.Contains("三天")) key = "officer_deadline";
                else if (body != null && body.Contains("烧掉整座")) key = "officer_burn";
                else if (body != null && body.Contains("文化")) key = "officer_threat";
                else if (body != null && body.Contains("别多事")) key = "dismiss";
                else key = "officer";
            }
            else if (title == "王砚") key = body != null && body.Contains("王家的人") ? "wang_street" : "wang";

            if (string.IsNullOrEmpty(key))
            {
                if (source != null) source.Stop();
                return;
            }

            AudioClip clip = Resources.Load<AudioClip>("Act1Audio/" + key);
            if (clip == null)
            {
                if (source != null) source.Stop();
                return;
            }

            source.Stop();
            source.loop = false;
            source.clip = clip;
            source.Play();
            Debug.Log($"[Act1] 播放语音 {key}");
        }

        public void PlayArgue()
        {
            AudioClip clip = Resources.Load<AudioClip>("Act1Audio/argue");
            if (clip == null) return;
            source.clip = clip;
            source.loop = true;
            source.Play();
            Debug.Log("[Act1] 播放三派争吵音频");
        }

        public void PlayBoots()
        {
            int sampleRate = 22050;
            int length = (int)(sampleRate * 1.4f);
            float[] samples = new float[length];
            for (int i = 0; i < length; i++)
            {
                float t = (float)i / sampleRate;
                float pulse = Mathf.Repeat(t, 0.32f);
                float step = pulse < 0.09f ? Mathf.Sin(pulse * 2f * Mathf.PI * 95f) * (1f - pulse / 0.09f) : 0f;
                samples[i] = step * 0.35f + Random.Range(-0.02f, 0.02f);
            }
            AudioClip clip = AudioClip.Create("BootSteps", length, 1, sampleRate, false);
            clip.SetData(samples, 0);
            source.PlayOneShot(clip, 0.9f);
            Debug.Log("[Act1] 播放皮靴脚步声");
        }

        public void Stop()
        {
            source.Stop();
            source.loop = false;
        }
    }
}
