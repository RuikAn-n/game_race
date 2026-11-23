using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Rupu
{
    public class Act1Director : MonoBehaviour
    {
        public enum Stage
        {
            Arrival,
            Clan,
            Memorial,
            Officer,
            Pages,
            Factions,
            Spring,
            Street,
            Fading,
            Ended
        }

        private class DialogueLine
        {
            public string title;
            public string body;
            public Action onDone;
        }

        public Stage stage = Stage.Arrival;
        public bool PagesMended { get; private set; }
        public bool FlagTouched { get; private set; }
        public string Objective { get; private set; } = "回到祠堂";
        public Act1Interactable flagPoint;
        public Act1Interactable clanPoint;
        public Act1Interactable memorialPoint;
        public Transform pagesPoint;
        public List<Act1Interactable> factionPoints = new List<Act1Interactable>();
        public Transform[] factionActors;
        public Transform clanLeader;
        public Transform elder;
        public Transform elderStop;   // 族老带路进祠堂后的站位；为空时走到族亲互动点前 2m
        public Transform shrineOfficer;
        public Transform[] shrineGuards;
        public Transform streetExit;
        public Vector3 factionCenter = new Vector3(0f, 1f, -4f);
        public Vector3 clanStop = new Vector3(0f, 1.2f, -3f);
        public Act1Player player;
        public Act1Voice voice;
        private bool argumentVisible;
        private string argumentText = "";

        private readonly HashSet<string> talked = new HashSet<string>();
        private readonly Queue<DialogueLine> dialogueQueue = new Queue<DialogueLine>();
        private DialogueLine currentLine;
        private bool dialogueActive;
        private bool streetNarrationShown;
        private Transform guideTarget;
        private string guideLabel = "";
        private bool eventBlock;
        private float fade;
        private string banner = "";
        private bool showEndCard;
        private float introUntil;
        private GUIStyle titleStyle;
        private GUIStyle bodyStyle;
        private GUIStyle objectiveStyle;
        private GUIStyle bannerStyle;
        private Font font;

        public bool BlocksMovement =>
            stage == Stage.Arrival ||
            stage == Stage.Officer ||
            stage == Stage.Spring ||
            stage == Stage.Fading ||
            stage == Stage.Ended ||
            dialogueActive ||
            eventBlock;

        public void SetEventBlock(bool value)
        {
            eventBlock = value;
        }

        public void Tell(string title, string body, Action onDone = null)
        {
            ShowDialogue(title, body, onDone);
        }

        private void Start()
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;

            if (voice == null) voice = FindObjectOfType<Act1Voice>();
            if (voice == null) voice = gameObject.AddComponent<Act1Voice>();

            if (flagPoint != null) flagPoint.gameObject.SetActive(false);
            if (clanPoint != null) clanPoint.gameObject.SetActive(false);
            if (memorialPoint != null) memorialPoint.gameObject.SetActive(false);
            if (shrineOfficer != null) shrineOfficer.gameObject.SetActive(false);
            if (shrineGuards != null)
            {
                foreach (Transform guard in shrineGuards)
                {
                    if (guard != null) guard.gameObject.SetActive(false);
                }
            }
            foreach (Act1Interactable point in factionPoints)
            {
                if (point != null) point.gameObject.SetActive(false);
            }

            introUntil = Time.unscaledTime + 8f;
            ShowDialogue("旁白", "1941年4月19日，温州沦陷。日军飞机低低掠过永昌堡，本该在今日举行的春祭，被警报和哭声截断。你带着半本《英桥王氏族谱》，回到祠堂。", () =>
            {
                if (elder != null && player != null) player.LookAt(elder.position + Vector3.up * 1.4f, 3f);
                ShowDialogue("族老", "“王砚，你回来得不是时候。你父亲王世清，一年前就没了音信。谱上他的名字，被人用墨涂黑了。”", () =>
                {
                    ShowDialogue("族老", "“有人说他投了日本人，也有人说他替山里送过药。族里为这句话，已经吵了一年。”", () =>
                    {
                        ShowDialogue("族老", "“跟我来。进祠堂说，别站在门口让日本人看见。”", () =>
                        {
                            StartCoroutine(ElderLeadIntoHall());
                        });
                    });
                });
            });
        }

        private IEnumerator ElderLeadIntoHall()
        {
            stage = Stage.Clan;
            Objective = "跟着族老进祠堂";
            if (clanPoint != null) clanPoint.gameObject.SetActive(false);

            Vector3 start = elder != null ? elder.position : new Vector3(-20f, 0f, 17.5f);
            Vector3 target = elderStop != null
                ? elderStop.position
                : clanPoint != null
                    ? clanPoint.transform.position + Vector3.forward * 2f
                    : start + Vector3.forward * 10f;
            target.y = start.y;
            if (player != null) player.LookAt(target + Vector3.up * 1.5f, 3f);

            float t = 0f;
            while (t < 1f)
            {
                t += Time.deltaTime / 3.2f;
                if (elder != null)
                {
                    elder.position = Vector3.Lerp(start, target, Mathf.SmoothStep(0f, 1f, t));
                }
                yield return null;
            }

            Objective = "在祠堂里和族亲说话";
            if (clanPoint != null) clanPoint.gameObject.SetActive(true);
            Debug.Log("[Act1] 族老带路进祠堂，族亲交谈解锁");
        }

        private void UpdateGuideTarget()
        {
            Transform target = null;
            string label = "";

            switch (stage)
            {
                case Stage.Arrival:
                    if (elder != null) { target = elder; label = "族老"; }
                    break;
                case Stage.Clan:
                    if (clanPoint != null) { target = clanPoint.transform; label = "族亲"; }
                    break;
                case Stage.Memorial:
                    if (memorialPoint != null) { target = memorialPoint.transform; label = "父亲灵位"; }
                    break;
                case Stage.Pages:
                    if (pagesPoint != null) { target = pagesPoint; label = "残谱拼合"; }
                    break;
                case Stage.Factions:
                    float best = float.MaxValue;
                    foreach (Act1Interactable point in factionPoints)
                    {
                        if (point == null || talked.Contains(point.id)) continue;
                        float distance = player != null ? Vector3.Distance(player.transform.position, point.transform.position) : point.transform.position.sqrMagnitude;
                        if (distance < best) { best = distance; target = point.transform; label = point.label; }
                    }
                    break;
                case Stage.Officer:
                    if (shrineOfficer != null) { target = shrineOfficer; label = "日本军官"; }
                    break;
                case Stage.Street:
                    if (flagPoint != null) { target = flagPoint.transform; label = "环海楼 · 残旗"; }
                    break;
            }

            guideTarget = target;
            guideLabel = label;
        }

        private void Update()
        {
            UpdateGuideTarget();

            if (dialogueActive && Input.GetKeyDown(KeyCode.Space))
            {
                if (voice == null || !voice.IsSpeaking) AdvanceDialogue();
            }

            if (stage == Stage.Street && !streetNarrationShown && player != null)
            {
                bool outside = streetExit != null
                    ? Vector3.Distance(player.transform.position, streetExit.position) <= 4f
                    : player.transform.position.z > 33.5f;
                if (outside)
                {
                    streetNarrationShown = true;
                    ShowDialogue("旁白", "你走出祠堂院门。街上都是日军，飞机在头顶盘旋，街尾已经有火光，哭声和惨叫声一阵阵传过来。");
                    Debug.Log("[Act1] 玩家走出祠堂，街景旁白触发");
                }
            }

            if (stage == Stage.Street && player != null && flagPoint != null)
            {
                float distance = Vector3.Distance(player.transform.position, flagPoint.transform.position);
                Objective = $"沿街往环海楼走（{distance:0}m）";
            }

            if (stage == Stage.Ended && Input.GetKeyDown(KeyCode.R))
            {
                SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
            }
        }

        public void CompleteInteraction(string id)
        {
            if (id == "clan" && stage == Stage.Clan)
            {
                stage = Stage.Memorial;
                Objective = "去父亲灵前上炷香";
                if (memorialPoint != null) memorialPoint.gameObject.SetActive(true);
                ShowDialogue("族中冷遇", "“你爹投了日本人，你还有脸回来？”");
                ShowDialogue("族中亲善", "“孩子刚回来，先让他给他爹上炷香。”");
                ShowDialogue("族老", "“王砚，别听他们吵。先跟我来，给你父亲上炷香。”");
                Debug.Log("[Act1] 族亲冷遇/亲善完成，祭拜解锁");
                return;
            }

            if (id == "memorial" && stage == Stage.Memorial)
            {
                if (player != null && memorialPoint != null) player.LookAt(memorialPoint.transform.position + Vector3.up * 1.4f, 3f);
                ShowDialogue("王砚", "爹，我回来了。");
                ShowDialogue("族老", "“上面供奉的两位，是王沛公、王叔杲公。一个守过堡，一个建过堡。你父亲在下面这一排。你小时候，我抱你认过他们的牌位。”");
                ShowDialogue("王砚", "我记得。谱里见过他们的名字。");
                ShowDialogue("族老", "“谱在，人就在。”", BeginOfficerArrival);
                return;
            }

            if (id == "pages" && stage == Stage.Pages)
            {
                PagesMended = true;
                stage = Stage.Factions;
                Objective = "在祠堂里听三拨人说话（0/3）";
                ShowDialogue("王砚", "三张散页拼回去了。父亲王世清的名字被墨涂黑，墨还没干。");
                ShowDialogue("旁白", "族里有人说他投了日本人，也有人说他替山里送过药。父亲的失踪，和这本谱一起压在你手上。");
                foreach (Act1Interactable point in factionPoints)
                {
                    if (point != null) point.gameObject.SetActive(true);
                }
                Debug.Log("[Act1] 残谱拼合完成，三股人交谈解锁");
                return;
            }

            if (stage == Stage.Factions && id.StartsWith("faction_"))
            {
                if (!talked.Add(id)) return;

                if (id == "faction_jiao")
                {
                    ShowDialogue("交谱派族老", "“把谱交出去。日本人要的是谱，不是人。三百口人，不能陪一本谱死。”");
                    ShowDialogue("交谱派族老", "“王砚，你在上海见过他们的枪。别拿全堡去赌。”", CheckThreeTalks);
                }
                else if (id == "faction_shao")
                {
                    ShowDialogue("烧谱派青年", "“交出去，他们拿谱作证，王氏就断了根。”");
                    ShowDialogue("烧谱派青年", "“烧了！至少不留给外人。”", CheckThreeTalks);
                }
                else if (id == "faction_cang")
                {
                    ShowDialogue("藏谱派妇人", "“藏进夹墙、井里、匾后。等天亮，人活着，谱还能补。”");
                    ShowDialogue("藏谱派妇人", "“你爹的事还没查清，谱不能先没了。”", CheckThreeTalks);
                }

                Objective = $"在祠堂里听三拨人说话（{talked.Count}/3）";
                return;
            }

            if (id == "flag" && stage == Stage.Street)
            {
                FlagTouched = true;
                stage = Stage.Fading;
                Objective = "";
                ShowDialogue("王砚", "旗杆斜倒在石阶上，旗面沾着旧血。指尖一碰，血还是温的。");
                StartCoroutine(FadeToMing());
                Debug.Log("[Act1] 残旗入谱，开始穿越");
            }
        }

        private void BeginOfficerArrival()
        {
            stage = Stage.Officer;
            Objective = "";
            if (player != null)
            {
                Vector3 entry = shrineOfficer != null
                    ? shrineOfficer.position + Vector3.forward * 6f + Vector3.up * 2f
                    : new Vector3(0f, 2f, 33f);
                player.LookAt(entry, 4f);
            }
            ShowDialogue("旁白", "话音未落，院门外传来皮靴踏水的声音。先是一双，再是三四双，越来越近。", () =>
            {
                StartCoroutine(OfficerWalkIn());
            });
        }

        private IEnumerator OfficerWalkIn()
        {
            if (shrineOfficer == null)
            {
                ShowOfficerLines();
                yield break;
            }

            Vector3 officerTarget = shrineOfficer.position;
            Vector3[] guardTargets = new Vector3[2];
            if (shrineGuards != null)
            {
                for (int i = 0; i < shrineGuards.Length && i < 2; i++)
                {
                    if (shrineGuards[i] != null) guardTargets[i] = shrineGuards[i].position;
                }
            }

            shrineOfficer.gameObject.SetActive(true);
            Vector3 officerEntry = officerTarget + Vector3.forward * 6f;
            shrineOfficer.position = officerEntry;
            if (shrineGuards != null)
            {
                for (int i = 0; i < shrineGuards.Length; i++)
                {
                    if (shrineGuards[i] == null) continue;
                    shrineGuards[i].gameObject.SetActive(true);
                    shrineGuards[i].position = guardTargets[i] + Vector3.forward * 6f;
                }
            }

            if (voice != null) voice.PlayBoots();
            if (player != null) player.LookAt(officerEntry + Vector3.up * 1.2f, 3f);

            float t = 0f;
            while (t < 1f)
            {
                t += Time.deltaTime / 2.4f;
                float smooth = Mathf.SmoothStep(0f, 1f, t);
                shrineOfficer.position = Vector3.Lerp(shrineOfficer.position, officerTarget, smooth);
                if (shrineGuards != null)
                {
                    for (int i = 0; i < shrineGuards.Length && i < 2; i++)
                    {
                        if (shrineGuards[i] == null) continue;
                        shrineGuards[i].position = Vector3.Lerp(shrineGuards[i].position, guardTargets[i], smooth);
                    }
                }
                yield return null;
            }

            if (player != null) player.LookAt(shrineOfficer.position + Vector3.up * 1.4f, 4f);
            ShowOfficerLines();
        }

        private void ShowOfficerLines()
        {
            ShowDialogue("日本军官", "“你就是王砚？从上海回来的？”");
            ShowDialogue("族老", "“太君，孩子刚回来，什么都不懂。”");
            ShowDialogue("日本军官", "“我读过《王氏族约》。‘谱在，人就在’，说得好。那就把谱交给我，我替你们保存。”");
            ShowDialogue("王秉之", "“谱是王氏的，不交给外人。”");
            ShowDialogue("日本军官", "“外人？我比你们更懂它。”");
            ShowDialogue("日本军官", "“不交，就烧掉整座祠堂。”");
            ShowDialogue("族老", "“太君，容我们商量商量……”");
            ShowDialogue("王秉之", "“不必商量。谱不能交。”");
            ShowDialogue("日本军官", "“三天。三天后我来取。”");
            ShowDialogue("旁白", "军官转身走出祠堂。皮靴声远了，春祭没有继续，香案上的灰落了一层。", () =>
            {
                StartCoroutine(OfficerLeave());
            });
        }

        private IEnumerator OfficerLeave()
        {
            if (shrineOfficer == null)
            {
                stage = Stage.Pages;
                Objective = "进祠堂，把半本族谱放上供桌";
                yield break;
            }

            Vector3 officerStart = shrineOfficer.position;
            Vector3 officerExit = officerStart + Vector3.forward * 6f;
            Vector3[] guardStarts = new Vector3[2];
            Vector3[] guardExits = new Vector3[2];
            if (shrineGuards != null)
            {
                for (int i = 0; i < shrineGuards.Length && i < 2; i++)
                {
                    if (shrineGuards[i] == null) continue;
                    guardStarts[i] = shrineGuards[i].position;
                    guardExits[i] = guardStarts[i] + Vector3.forward * 6f;
                }
            }

            if (voice != null) voice.PlayBoots();
            float t = 0f;
            while (t < 1f)
            {
                t += Time.deltaTime / 2f;
                float smooth = Mathf.SmoothStep(0f, 1f, t);
                shrineOfficer.position = Vector3.Lerp(officerStart, officerExit, smooth);
                if (shrineGuards != null)
                {
                    for (int i = 0; i < shrineGuards.Length && i < 2; i++)
                    {
                        if (shrineGuards[i] == null) continue;
                        shrineGuards[i].position = Vector3.Lerp(guardStarts[i], guardExits[i], smooth);
                    }
                }
                yield return null;
            }

            shrineOfficer.gameObject.SetActive(false);
            if (shrineGuards != null)
            {
                foreach (Transform guard in shrineGuards)
                {
                    if (guard != null) guard.gameObject.SetActive(false);
                }
            }

            stage = Stage.Pages;
            Objective = "进祠堂，把半本族谱放上供桌";
            Debug.Log("[Act1] 日本军官离开，残谱拼合解锁");
        }

        private void CheckThreeTalks()
        {
            if (talked.Count >= 3 && stage == Stage.Factions)
            {
                StartCoroutine(SpringArgument());
            }
        }

        private IEnumerator SpringArgument()
        {
            stage = Stage.Spring;
            Objective = "";
            Debug.Log("[Act1] 三派谈完，春祭争执开始");

            yield return AnimateArgument();
            yield return MoveLeaderThenStop();
        }

        private IEnumerator MoveLeaderThenStop()
        {
            if (player != null && clanLeader != null) player.LookAt(clanLeader.position + Vector3.up * 1.4f, 3.5f);

            if (clanLeader != null)
            {
                Vector3 start = clanLeader.position;
                Vector3 end = clanStop;
                float t = 0f;
                while (t < 1f)
                {
                    t += Time.deltaTime * 1.4f;
                    clanLeader.position = Vector3.Lerp(start, end, t);
                    yield return null;
                }
            }

            ShowDialogue("王秉之", "“都住口！春祭到此为止。谱不能交，也不能烧。谁再提一句交谱，先出这个祠堂。王砚，你出去走走。”", () =>
            {
                stage = Stage.Street;
                Objective = "沿街往环海楼走";
                if (flagPoint != null) flagPoint.gameObject.SetActive(true);
                streetNarrationShown = false;
                Debug.Log("[Act1] 族长结束春祭，街市解锁");
            });
        }

        private IEnumerator AnimateArgument()
        {
            argumentVisible = true;
            argumentText = "交谱派：交出去！三百口人不能陪一本谱死！";
            if (voice != null) voice.PlayArgue();
            if (player != null) player.LookAt(factionCenter + Vector3.up * 1.5f, 11f);

            if (factionActors == null || factionActors.Length == 0)
            {
                yield return new WaitForSeconds(10f);
                argumentVisible = false;
                yield break;
            }

            Vector3[] starts = new Vector3[factionActors.Length];
            Vector3 center = factionCenter;
            for (int i = 0; i < factionActors.Length; i++)
            {
                if (factionActors[i] != null) starts[i] = factionActors[i].position;
            }

            float elapsed = 0f;
            while (elapsed < 10f)
            {
                elapsed += Time.deltaTime;
                if (elapsed < 2.5f) argumentText = "交谱派：交出去！三百口人不能陪一本谱死！";
                else if (elapsed < 5f) argumentText = "烧谱派：烧了！不能留给日本人！";
                else if (elapsed < 7.5f) argumentText = "藏谱派：藏起来！人活着，谱还能补！";
                else argumentText = "三拨人同时开口，香案被撞翻……";

                float t = Mathf.Clamp01(elapsed / 3f);
                for (int i = 0; i < factionActors.Length; i++)
                {
                    if (factionActors[i] == null) continue;
                    // 三拨人各自朝中心挤过去（以中心为轴左右排开，避免撞成一团）
                    Vector3 target = Vector3.Lerp(starts[i], center + new Vector3((i - (factionActors.Length - 1) * 0.5f) * 1.2f, 0f, 0f), 0.35f);
                    factionActors[i].position = Vector3.Lerp(starts[i], target, t) + Vector3.up * Mathf.Abs(Mathf.Sin(Time.time * 18f + i)) * 0.04f;
                }

                yield return null;
            }

            argumentVisible = false;
            if (voice != null) voice.Stop();
        }

        private void ShowDialogue(string title, string body, Action onDone = null)
        {
            DialogueLine line = new DialogueLine { title = title, body = body, onDone = onDone };
            if (dialogueActive)
            {
                dialogueQueue.Enqueue(line);
                return;
            }

            currentLine = line;
            dialogueActive = true;
            if (voice != null) voice.PlayFor(line.title, line.body);
        }

        private void AdvanceDialogue()
        {
            if (!dialogueActive) return;
            if (voice != null && voice.IsSpeaking) return;

            Action done = currentLine != null ? currentLine.onDone : null;
            dialogueActive = false;
            currentLine = null;

            if (dialogueQueue.Count > 0)
            {
                currentLine = dialogueQueue.Dequeue();
                dialogueActive = true;
                if (voice != null) voice.PlayFor(currentLine.title, currentLine.body);
            }
            else
            {
                done?.Invoke();
            }
        }

        private IEnumerator FadeToMing()
        {
            while (fade < 1f)
            {
                fade = Mathf.MoveTowards(fade, 1f, Time.unscaledDeltaTime * 1.4f);
                yield return null;
            }

            banner = "嘉靖三十九年 · 永昌堡";
            yield return new WaitForSecondsRealtime(1.8f);

            banner = "第一幕 · 完";
            showEndCard = true;
            stage = Stage.Ended;
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            Debug.Log("[Act1] 第一幕完成：归堡");
        }

        private void OnGUI()
        {
            EnsureStyles();

            if (Time.unscaledTime < introUntil && (stage == Stage.Arrival || stage == Stage.Pages))
            {
                GUI.Label(new Rect(0f, 66f, Screen.width, 32f), "1941年4月19日 · 温州沦陷", bannerStyle);
                GUI.Label(new Rect(0f, 100f, Screen.width, 24f), "永昌堡 · 王氏宗祠", objectiveStyle);
            }

            if (!string.IsNullOrEmpty(Objective) && stage != Stage.Ended)
            {
                Rect objective = new Rect(24f, 22f, 560f, 34f);
                GUI.color = new Color(0.04f, 0.03f, 0.02f, 0.72f);
                GUI.DrawTexture(objective, Texture2D.whiteTexture);
                GUI.color = Color.white;
                GUI.Label(new Rect(objective.x + 12f, objective.y + 6f, 536f, 24f), $"第一幕 · {Objective}", objectiveStyle);
            }

            if (argumentVisible)
            {
                GUI.Label(new Rect(0f, Screen.height - 120f, Screen.width, 34f), argumentText, bannerStyle);
            }

            if (!dialogueActive && guideTarget != null && stage != Stage.Fading && stage != Stage.Ended)
            {
                Camera mainCamera = Camera.main;
                if (mainCamera != null)
                {
                    Vector3 world = guideTarget.position + Vector3.up * 2f;
                    Vector3 screen = mainCamera.WorldToScreenPoint(world);
                    float distance = player != null ? Vector3.Distance(player.transform.position, guideTarget.position) : 0f;
                    float x = screen.x;
                    float y = Screen.height - screen.y;
                    bool visible = screen.z > 0f && x > 80f && x < Screen.width - 80f && y > 90f && y < Screen.height - 90f;
                    if (!visible)
                    {
                        x = Mathf.Clamp(x, 90f, Screen.width - 90f);
                        y = screen.z > 0f ? Mathf.Clamp(y, 100f, Screen.height - 100f) : 130f;
                    }
                    string guide = visible
                        ? $"{guideLabel}  {distance:0}m"
                        : $"↑ {guideLabel}  {distance:0}m";
                    Rect label = new Rect(x - 120f, y - 16f, 240f, 30f);
                    GUI.color = new Color(0.04f, 0.03f, 0.02f, 0.72f);
                    GUI.DrawTexture(label, Texture2D.whiteTexture);
                    GUI.color = Color.white;
                    GUI.Label(new Rect(label.x + 8f, label.y + 4f, 224f, 24f), guide, objectiveStyle);
                }
            }

            if (dialogueActive && stage != Stage.Fading && stage != Stage.Ended)
            {
                Rect panel = new Rect(Screen.width / 2f - 390f, Screen.height - 210f, 780f, 140f);
                GUI.color = new Color(0.04f, 0.03f, 0.02f, 0.92f);
                GUI.DrawTexture(panel, Texture2D.whiteTexture);
                GUI.color = Color.white;
                GUI.Label(new Rect(panel.x + 20f, panel.y + 12f, 740f, 26f), currentLine != null ? currentLine.title : "", titleStyle);
                GUI.Label(new Rect(panel.x + 20f, panel.y + 42f, 740f, 64f), currentLine != null ? currentLine.body : "", bodyStyle);
                GUI.Label(new Rect(panel.x + 20f, panel.y + 110f, 740f, 22f), voice != null && voice.IsSpeaking ? "语音播放中，听完才能继续……" : "空格 继续", objectiveStyle);
            }

            if (stage == Stage.Fading || stage == Stage.Ended)
            {
                GUI.color = new Color(0f, 0f, 0f, Mathf.Clamp01(fade));
                GUI.DrawTexture(new Rect(0f, 0f, Screen.width, Screen.height), Texture2D.whiteTexture);
                GUI.color = Color.white;

                if (!string.IsNullOrEmpty(banner))
                {
                    GUI.Label(new Rect(0f, Screen.height / 2f - 30f, Screen.width, 60f), banner, bannerStyle);
                }

                if (showEndCard)
                {
                    GUI.Label(new Rect(0f, Screen.height / 2f + 46f, Screen.width, 30f), "按 R 重看第一幕", bodyStyle);
                }
            }
        }

        private void EnsureStyles()
        {
            if (titleStyle != null) return;

            if (font == null) font = Font.CreateDynamicFontFromOSFont("Microsoft YaHei", 20);
            titleStyle = new GUIStyle(GUI.skin.label);
            titleStyle.font = font;
            titleStyle.fontSize = 20;
            titleStyle.fontStyle = FontStyle.Bold;
            titleStyle.normal.textColor = new Color(0.96f, 0.88f, 0.70f);

            bodyStyle = new GUIStyle(GUI.skin.label);
            bodyStyle.font = font;
            bodyStyle.fontSize = 18;
            bodyStyle.wordWrap = true;
            bodyStyle.normal.textColor = new Color(0.92f, 0.88f, 0.78f);

            objectiveStyle = new GUIStyle(bodyStyle);
            objectiveStyle.fontSize = 17;

            bannerStyle = new GUIStyle(GUI.skin.label);
            bannerStyle.font = font;
            bannerStyle.fontSize = 30;
            bannerStyle.fontStyle = FontStyle.Bold;
            bannerStyle.alignment = TextAnchor.MiddleCenter;
            bannerStyle.normal.textColor = new Color(0.92f, 0.84f, 0.66f);
        }
    }
}
