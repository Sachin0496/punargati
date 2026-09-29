// Coaching language: cue banners and voice prompts. UI chrome stays English.
export const LANGS = {
  en: { name: "English", voice: "en-IN" },
  hi: { name: "हिन्दी", voice: "hi-IN" },
  ta: { name: "தமிழ்", voice: "ta-IN" },
  te: { name: "తెలుగు", voice: "te-IN" },
  kn: { name: "ಕನ್ನಡ", voice: "kn-IN" },
  mr: { name: "मराठी", voice: "mr-IN" },
  bn: { name: "বাংলা", voice: "bn-IN" },
};

const CUES = {
  go_further: { en: "Go a little further", hi: "थोड़ा और आगे जाइए", ta: "இன்னும் கொஞ்சம் மேலே செல்லுங்கள்", te: "ఇంకొంచెం ముందుకు వెళ్ళండి", kn: "ಇನ್ನೂ ಸ್ವಲ್ಪ ಮುಂದೆ ಹೋಗಿ", mr: "थोडं आणखी पुढे जा", bn: "আরেকটু বেশি করুন" },
  slow_down: { en: "Slow down, control the movement", hi: "धीरे करें, नियंत्रण से", ta: "மெதுவாக, கட்டுப்பாட்டுடன் செய்யுங்கள்", te: "నెమ్మదిగా, నియంత్రణతో చేయండి", kn: "ನಿಧಾನವಾಗಿ, ನಿಯಂತ್ರಣದಿಂದ ಮಾಡಿ", mr: "हळू करा, नियंत्रणाने", bn: "ধীরে, নিয়ন্ত্রণ রেখে করুন" },
  great_rep: { en: "Great rep!", hi: "बहुत बढ़िया!", ta: "மிகச் சிறப்பு!", te: "చాలా బాగుంది!", kn: "ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ!", mr: "खूप छान!", bn: "দারুণ হয়েছে!" },
  chest_up: { en: "Keep your chest up", hi: "छाती ऊपर रखें", ta: "மார்பை நிமிர்த்தி வையுங்கள்", te: "ఛాతీని పైకి ఉంచండి", kn: "ಎದೆಯನ್ನು ಮೇಲಕ್ಕೆ ಇಡಿ", mr: "छाती वर ठेवा", bn: "বুক উঁচু রাখুন" },
  knees_out: { en: "Push your knees outward", hi: "घुटनों को बाहर की ओर रखें", ta: "முழங்கால்களை வெளிப்புறமாக வையுங்கள்", te: "మోకాళ్ళను బయటకు ఉంచండి", kn: "ಮೊಣಕಾಲುಗಳನ್ನು ಹೊರಕ್ಕೆ ಇಡಿ", mr: "गुडघे बाहेरच्या बाजूला ठेवा", bn: "হাঁটু বাইরের দিকে রাখুন" },
  sit_tall: { en: "Sit tall", hi: "सीधे बैठिए", ta: "நிமிர்ந்து உட்காருங்கள்", te: "నిటారుగా కూర్చోండి", kn: "ನೇರವಾಗಿ ಕುಳಿತುಕೊಳ್ಳಿ", mr: "ताठ बसा", bn: "সোজা হয়ে বসুন" },
  straight_elbow: { en: "Keep your elbow straight", hi: "कोहनी सीधी रखें", ta: "முழங்கையை நேராக வையுங்கள்", te: "మోచేయిని నిటారుగా ఉంచండి", kn: "ಮೊಣಕೈಯನ್ನು ನೇರವಾಗಿ ಇಡಿ", mr: "कोपर सरळ ठेवा", bn: "কনুই সোজা রাখুন" },
  no_lean_back: { en: "Don't lean back", hi: "पीछे मत झुकिए", ta: "பின்னால் சாயாதீர்கள்", te: "వెనక్కి వంగకండి", kn: "ಹಿಂದಕ್ಕೆ ಬಾಗಬೇಡಿ", mr: "मागे झुकू नका", bn: "পিছনে হেলবেন না" },
  no_shrug: { en: "Relax your shoulder, don't shrug", hi: "कंधा ढीला रखें, ऊपर न उठाएँ", ta: "தோளைத் தளர்வாக வையுங்கள், உயர்த்தாதீர்கள்", te: "భుజాన్ని సడలించండి, పైకి ఎత్తకండి", kn: "ಭುಜವನ್ನು ಸಡಿಲವಾಗಿಡಿ, ಮೇಲಕ್ಕೆತ್ತಬೇಡಿ", mr: "खांदा सैल ठेवा, वर उचलू नका", bn: "কাঁধ আলগা রাখুন, উঁচু করবেন না" },
  stand_tall: { en: "Stand tall, don't lean", hi: "सीधे खड़े रहिए, झुकिए मत", ta: "நேராக நில்லுங்கள், சாயாதீர்கள்", te: "నిటారుగా నిలబడండి, వంగకండి", kn: "ನೇರವಾಗಿ ನಿಲ್ಲಿ, ಬಾಗಬೇಡಿ", mr: "ताठ उभे राहा, झुकू नका", bn: "সোজা হয়ে দাঁড়ান, হেলবেন না" },
  take_rest: { en: "You're tiring. Take a short rest", hi: "आप थक रहे हैं, थोड़ा आराम कीजिए", ta: "நீங்கள் சோர்வடைகிறீர்கள், சற்று ஓய்வெடுங்கள்", te: "మీరు అలసిపోతున్నారు, కొంచెం విశ్రాంతి తీసుకోండి", kn: "ನೀವು ದಣಿಯುತ್ತಿದ್ದೀರಿ, ಸ್ವಲ್ಪ ವಿಶ್ರಾಂತಿ ತೆಗೆದುಕೊಳ್ಳಿ", mr: "तुम्ही थकत आहात, थोडी विश्रांती घ्या", bn: "আপনি ক্লান্ত হয়ে পড়ছেন, একটু বিশ্রাম নিন" },
  straight_knees: { en: "Keep your knees straight", hi: "घुटने सीधे रखें", ta: "முழங்கால்களை நேராக வையுங்கள்", te: "మోకాళ్ళను నిటారుగా ఉంచండి", kn: "ಮೊಣಕಾಲುಗಳನ್ನು ನೇರವಾಗಿ ಇಡಿ", mr: "गुडघे सरळ ठेवा", bn: "হাঁটু সোজা রাখুন" },
  elbow_close: { en: "Keep your upper arm by your side", hi: "बाँह को शरीर के पास रखें", ta: "கையை உடலோடு ஒட்டி வையுங்கள்", te: "చేతిని శరీరానికి దగ్గరగా ఉంచండి", kn: "ತೋಳನ್ನು ದೇಹದ ಹತ್ತಿರ ಇಡಿ", mr: "हात शरीराजवळ ठेवा", bn: "হাত শরীরের কাছে রাখুন" },
  step_back: { en: "Step back so your whole body is visible", hi: "थोड़ा पीछे हटिए ताकि पूरा शरीर दिखे", ta: "முழு உடலும் தெரிய சற்று பின்னால் செல்லுங்கள்", te: "శరీరం మొత్తం కనిపించేలా కొంచెం వెనక్కి జరగండి", kn: "ಇಡೀ ದೇಹ ಕಾಣುವಂತೆ ಸ್ವಲ್ಪ ಹಿಂದೆ ಸರಿಯಿರಿ", mr: "संपूर्ण शरीर दिसेल असे थोडे मागे सरका", bn: "পুরো শরীর দেখা যায় এমনভাবে একটু পিছিয়ে যান" },
  turn_side: { en: "Turn sideways to the camera", hi: "कैमरे की ओर बगल से खड़े होइए", ta: "கேமராவுக்குப் பக்கவாட்டில் திரும்புங்கள்", te: "కెమెరాకు పక్కకు తిరగండి", kn: "ಕ್ಯಾಮೆರಾಗೆ ಪಕ್ಕಕ್ಕೆ ತಿರುಗಿ", mr: "कॅमेऱ्याकडे बाजूने वळा", bn: "ক্যামেরার দিকে পাশ ফিরে দাঁড়ান" },
  face_camera: { en: "Please face the camera", hi: "कृपया कैमरे की ओर मुँह करें", ta: "கேமராவைப் பார்த்து நில்லுங்கள்", te: "దయచేసి కెమెరా వైపు చూడండి", kn: "ದಯವಿಟ್ಟು ಕ್ಯಾಮೆರಾದ ಕಡೆ ನೋಡಿ", mr: "कृपया कॅमेऱ्याकडे तोंड करा", bn: "অনুগ্রহ করে ক্যামেরার দিকে মুখ করুন" },
  test_countdown: { en: "Get ready", hi: "तैयार हो जाइए", ta: "தயாராகுங்கள்", te: "సిద్ధంగా ఉండండి", kn: "ಸಿದ್ಧರಾಗಿ", mr: "तयार व्हा", bn: "প্রস্তুত হন" },
  test_start: { en: "Go!", hi: "शुरू!", ta: "தொடங்குங்கள்!", te: "మొదలుపెట్టండి!", kn: "ಪ್ರಾರಂಭಿಸಿ!", mr: "सुरू करा!", bn: "শুরু করুন!" },
  test_end: { en: "Test complete", hi: "टेस्ट पूरा हुआ", ta: "சோதனை முடிந்தது", te: "పరీక్ష పూర్తయింది", kn: "ಪರೀಕ್ಷೆ ಮುಗಿಯಿತು", mr: "चाचणी पूर्ण झाली", bn: "পরীক্ষা শেষ" },
  timer_running: { en: "Timer started, hold steady", hi: "टाइमर शुरू, संतुलन बनाए रखें", ta: "நேரம் தொடங்கியது, சமநிலையை வையுங்கள்", te: "టైమర్ మొదలైంది, సమతుల్యంగా ఉండండి", kn: "ಟೈಮರ್ ಪ್ರಾರಂಭವಾಗಿದೆ, ಸಮತೋಲನ ಕಾಯ್ದುಕೊಳ್ಳಿ", mr: "टायमर सुरू झाला, तोल सांभाळा", bn: "টাইমার শুরু হয়েছে, ভারসাম্য রাখুন" },
  set_done: { en: "Set complete. Well done!", hi: "सेट पूरा हुआ। शाबाश!", ta: "செட் முடிந்தது. அருமை!", te: "సెట్ పూర్తయింది. శభాష్!", kn: "ಸೆಟ್ ಮುಗಿಯಿತು. ಶಭಾಷ್!", mr: "सेट पूर्ण झाला. शाब्बास!", bn: "সেট শেষ। শাবাশ!" },
  halfway: { en: "Halfway there", hi: "आधा हो गया", ta: "பாதி முடிந்தது", te: "సగం పూర్తయింది", kn: "ಅರ್ಧ ಮುಗಿಯಿತು", mr: "अर्धे झाले", bn: "অর্ধেক হয়ে গেছে" },
  start_ex: { en: "Let's begin", hi: "चलिए शुरू करते हैं", ta: "தொடங்குவோம்", te: "మొదలుపెడదాం", kn: "ಪ್ರಾರಂಭಿಸೋಣ", mr: "चला सुरू करूया", bn: "চলুন শুরু করি" },
};

let lang = "en";
let voiceOn = true;
let voices = [];
const loadVoices = () => { voices = window.speechSynthesis ? speechSynthesis.getVoices() : []; };
if (window.speechSynthesis) { loadVoices(); speechSynthesis.addEventListener("voiceschanged", loadVoices); }

export function setLang(l) { lang = LANGS[l] ? l : "en"; }
export function getLang() { return lang; }
export function setVoice(on) { voiceOn = on; if (!on && window.speechSynthesis) speechSynthesis.cancel(); }

export function cueText(key, l = lang) {
  const c = CUES[key];
  return c ? (c[l] || c.en) : key.replace(/_/g, " ");
}

export function voiceFor(l = lang) {
  // Only on-device voices: browsers also list cloud "Online (Natural)" voices, which would
  // send coaching text off the PC.
  const local = voices.filter(v => v.localService);
  const want = LANGS[l]?.voice || "en-IN";
  const base = want.split("-")[0];
  return local.find(v => v.lang === want) || local.find(v => v.lang?.replace("_", "-").startsWith(base)) || null;
}

let lastSpoken = 0;
export function speak(text, { priority = false } = {}) {
  if (!voiceOn || !window.speechSynthesis || !text) return;
  const now = performance.now();
  if (!priority && speechSynthesis.speaking && now - lastSpoken < 2500) return;
  const v = voiceFor();
  // No installed voice for this language: an English voice mangles Indic text, so stay silent.
  if (!v && lang !== "en") return;
  if (priority) speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(String(text));
  if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = "en-IN"; }
  u.rate = 1.0;
  speechSynthesis.speak(u);
  lastSpoken = now;
}

export function speakCue(key) { speak(cueText(key)); }

// Deterministic patient-language summary built from measured facts (vetted phrasing,
// no generative model involved), so non-English users never see garbled LLM prose.
const SUM = {
  en: { ex: "{name}: {reps} reps. Best range {best}°. Quality {q}/100.", up: "That is {d}° better than last time.", down: "{d}° less than last time.", same: "Same range as last time.", fault: "Next time: {fault}.", clean: "Form was clean. Well done!", test: "{name}: {score} {unit}." },
  hi: { ex: "{name}: {reps} दोहराव। सबसे अच्छा कोण {best}°। गुणवत्ता {q}/100।", up: "पिछली बार से {d}° बेहतर।", down: "पिछली बार से {d}° कम।", same: "पिछली बार जितना ही।", fault: "अगली बार ध्यान दें: {fault}।", clean: "फ़ॉर्म बिल्कुल सही था। शाबाश!", test: "{name}: {score} {unit}।" },
  ta: { ex: "{name}: {reps} முறை. சிறந்த கோணம் {best}°. தரம் {q}/100.", up: "கடந்த முறையை விட {d}° முன்னேற்றம்.", down: "கடந்த முறையை விட {d}° குறைவு.", same: "கடந்த முறை போலவே.", fault: "அடுத்த முறை கவனிக்க: {fault}.", clean: "உடல் நிலை சரியாக இருந்தது. அருமை!", test: "{name}: {score} {unit}." },
  te: { ex: "{name}: {reps} సార్లు. ఉత్తమ కోణం {best}°. నాణ్యత {q}/100.", up: "గతసారి కంటే {d}° మెరుగు.", down: "గతసారి కంటే {d}° తక్కువ.", same: "గతసారి లాగే.", fault: "తదుపరిసారి గమనించండి: {fault}.", clean: "భంగిమ సరిగ్గా ఉంది. శభాష్!", test: "{name}: {score} {unit}." },
  kn: { ex: "{name}: {reps} ಬಾರಿ. ಉತ್ತಮ ಕೋನ {best}°. ಗುಣಮಟ್ಟ {q}/100.", up: "ಕಳೆದ ಬಾರಿಗಿಂತ {d}° ಉತ್ತಮ.", down: "ಕಳೆದ ಬಾರಿಗಿಂತ {d}° ಕಡಿಮೆ.", same: "ಕಳೆದ ಬಾರಿಯಷ್ಟೇ.", fault: "ಮುಂದಿನ ಬಾರಿ ಗಮನಿಸಿ: {fault}.", clean: "ಭಂಗಿ ಸರಿಯಾಗಿತ್ತು. ಶಭಾಷ್!", test: "{name}: {score} {unit}." },
  mr: { ex: "{name}: {reps} वेळा. सर्वोत्तम कोन {best}°. गुणवत्ता {q}/100.", up: "मागच्या वेळेपेक्षा {d}° चांगले.", down: "मागच्या वेळेपेक्षा {d}° कमी.", same: "मागच्या वेळेइतकेच.", fault: "पुढच्या वेळी लक्ष द्या: {fault}.", clean: "पद्धत अगदी योग्य होती. शाब्बास!", test: "{name}: {score} {unit}." },
  bn: { ex: "{name}: {reps} বার। সেরা কোণ {best}°। মান {q}/100।", up: "গতবারের চেয়ে {d}° ভালো।", down: "গতবারের চেয়ে {d}° কম।", same: "গতবারের মতোই।", fault: "পরের বার খেয়াল রাখুন: {fault}।", clean: "ভঙ্গি একদম ঠিক ছিল। শাবাশ!", test: "{name}: {score} {unit}।" },
};
const fill = (t, o) => t.replace(/\{(\w+)\}/g, (_, k) => o[k] ?? "");

export function localSummary(f, l = lang) {
  const T = SUM[l] || SUM.en;
  if (f.kind !== "exercise") {
    let s = fill(T.test, { name: f.name, score: f.score, unit: f.unit });
    if (typeof f.delta === "number" && f.delta) s += " " + fill(f.delta > 0 ? T.up : T.down, { d: Math.abs(f.delta) }).replace("°", "");
    return s;
  }
  let s = fill(T.ex, { name: f.name, reps: f.reps, best: f.best ?? "—", q: f.quality });
  if (typeof f.delta === "number") s += " " + (f.delta === 0 ? T.same : fill(f.delta > 0 ? T.up : T.down, { d: Math.abs(f.delta) }));
  s += " " + (f.top_fault ? fill(T.fault, { fault: cueText(f.top_fault, l) }) : T.clean);
  return (f.rom_label || "").includes("%") ? s.replace(/°/g, "%") : s;
}

// Patient-facing interface in Hindi (other languages keep the English interface;
// their coaching cues and summaries are still localized above). Keyed by English text.
const UI_HI = {
  "Coach": "कोच", "Tests": "जाँच", "Progress": "प्रगति", "Plan": "योजना", "Ask coach": "कोच से पूछें", "Profile": "प्रोफ़ाइल",
  "Your physiotherapist's eyes, at home.": "घर पर, आपके फ़िज़ियोथेरेपिस्ट की नज़र।",
  "Pose tracking runs on the Snapdragon Hexagon NPU. Video never leaves this PC.": "शरीर की ट्रैकिंग Snapdragon Hexagon NPU पर होती है। वीडियो इस पीसी से बाहर नहीं जाता।",
  "Start camera": "कैमरा शुरू करें", "Use a video file": "वीडियो फ़ाइल चुनें", "Try the demo clip": "डेमो क्लिप देखें",
  "Place the laptop 2–3 m away so your whole body is in frame.": "लैपटॉप को 2–3 मीटर दूर रखें ताकि पूरा शरीर दिखे।",
  "Privacy view": "निजता दृश्य", "Voice": "आवाज़", "Precision": "सटीक मोड", "Tracker box": "ट्रैकर बॉक्स", "Change source": "स्रोत बदलें",
  "Exercises": "व्यायाम", "Finish & save": "पूरा करें और सहेजें", "How to do it": "कैसे करें",
  "Complete a rep to see its range, tempo and quality.": "एक दोहराव पूरा करें, फिर उसका कोण, समय और गुणवत्ता यहाँ दिखेगी।",
  "Standardised clinical tests": "मानक क्लिनिकल जाँच",
  "The same screening tests a physiotherapist runs with a stopwatch and goniometer — timed, counted and measured on-device.": "वही जाँच जो फ़िज़ियोथेरेपिस्ट स्टॉपवॉच और गोनियोमीटर से करते हैं। यहाँ समय, गिनती और माप अपने आप होते हैं।",
  "Start test": "जाँच शुरू करें", "Recovery progress": "रिकवरी की प्रगति", "Open report for my physio": "फ़िज़ियो के लिए रिपोर्ट खोलें",
  "Recent sessions": "हाल के सत्र", "sessions": "सत्र", "reps measured": "मापे गए दोहराव", "day streak": "लगातार दिन", "latest avg quality": "ताज़ा औसत गुणवत्ता",
  "Home exercise plan": "घर की व्यायाम योजना", "Current plan": "मौजूदा योजना", "Import prescription": "पर्चा जोड़ें",
  "Read prescription": "पर्चा पढ़ें", "Save as my plan": "मेरी योजना के रूप में सहेजें", "Start": "शुरू करें",
  "Ask your coach": "अपने कोच से पूछें", "Ask": "पूछें", "Save profile": "प्रोफ़ाइल सहेजें",
  "Name": "नाम", "Age": "उम्र", "Sex": "लिंग", "Condition": "स्थिति / बीमारी", "Affected side": "प्रभावित भाग",
  "Physiotherapist": "फ़िज़ियोथेरेपिस्ट", "Coaching language": "कोचिंग भाषा", "Notes": "टिप्पणी",
  "Coach summary": "कोच का सारांश", "Read aloud": "पढ़कर सुनाएँ", "Done": "ठीक है",
  "Rest": "आराम", "Moving": "गति में", "Not visible": "दिख नहीं रहा", "goal": "लक्ष्य", "per side": "हर तरफ़",
  "Quality": "गुणवत्ता", "Tempo": "समय", "Left": "बायाँ", "Right": "दायाँ",
  "Get into position": "सही स्थिति में आइए", "Get ready…": "तैयार हो जाइए…", "Go!": "शुरू!",
  "stands": "बार खड़े हुए", "s left": "सेकंड बाकी", "seconds on one leg": "सेकंड एक पैर पर", "best so far": "अब तक का सर्वश्रेष्ठ",
  "Sit on the chair, whole body in view": "कुर्सी पर बैठिए, पूरा शरीर दिखे", "Stand in view to begin": "शुरू करने के लिए कैमरे के सामने खड़े हों",
  "Lift one foot to start the clock": "घड़ी शुरू करने के लिए एक पैर उठाइए",
  "Within typical range": "सामान्य सीमा में", "Below average": "औसत से कम", "Fall-risk flag": "गिरने का जोखिम", "Limited range": "सीमित गति", "Recorded": "दर्ज",
  "Today's plan from": "आज की योजना:", "your physio": "आपके फ़िज़ियो",
  "Reps": "दोहराव", "Avg quality": "औसत गुणवत्ता", "Computed on": "कहाँ चला", "Score": "स्कोर", "Flag": "संकेत",
  "Best": "सर्वश्रेष्ठ", "saved": "सहेजा गया",
  // regions
  "Knee": "घुटना", "Function": "दैनिक कार्य", "Shoulder": "कंधा", "Elbow": "कोहनी", "Hip": "कूल्हा", "Ankle · precision": "टखना · सटीक",
  // exercise names
  "Mini squat": "मिनी स्क्वॉट", "Sit to stand": "बैठकर खड़े होना", "Seated knee extension": "बैठकर घुटना सीधा करना",
  "Shoulder forward raise": "कंधा आगे उठाना", "Shoulder side raise": "कंधा बगल में उठाना", "Elbow bend (curl)": "कोहनी मोड़ना",
  "Standing side leg raise": "खड़े होकर पैर बगल में उठाना", "Heel raise (calf raise)": "एड़ी उठाना", "Standing march": "खड़े होकर कदमताल",
  // tests
  "30-second chair stand": "30 सेकंड कुर्सी से उठना", "Single-leg balance": "एक पैर पर संतुलन", "Shoulder flexion range": "कंधे की आगे की गति",
  "Shoulder abduction range": "कंधे की बगल की गति", "Knee bend range": "घुटने के मोड़ की गति",
  // measures (range labels)
  "Knee flexion": "घुटने का मोड़", "Knee flexion at full extension (0 = straight)": "पूरा सीधा करने पर घुटने का कोण (0 = सीधा)",
  "Shoulder flexion": "कंधे को आगे उठाना", "Shoulder abduction": "कंधे को बगल में उठाना", "Elbow flexion": "कोहनी का मोड़",
  "Hip abduction": "कूल्हे को बगल में उठाना", "Hip flexion": "कूल्हे का मोड़", "Rise (% of full stand)": "उठना (पूरे खड़े होने का %)",
  "Ankle plantarflexion (foot angle)": "टखने का कोण (पंजों पर उठना)",
  // purposes
  "Quadriceps and gluteal strength after knee injury or replacement; fall prevention.": "घुटने की चोट या प्रत्यारोपण के बाद जांघ और कूल्हे की ताक़त; गिरने से बचाव।",
  "Functional leg strength; the movement behind independent daily living.": "रोज़मर्रा की ज़िंदगी के लिए पैरों की ताक़त, आत्मनिर्भरता की बुनियाद।",
  "Regain full knee extension after knee replacement, ACL repair or arthritis flare.": "घुटना बदलने, ACL सर्जरी या गठिया के बाद घुटने को फिर से पूरा सीधा करना।",
  "Frozen shoulder (common with diabetes), rotator-cuff and post-fracture rehab.": "फ्रोज़न शोल्डर (मधुमेह में आम), रोटेटर-कफ़ और फ्रैक्चर के बाद का पुनर्वास।",
  "Frozen shoulder and impingement rehab; tracks abduction range over weeks.": "फ्रोज़न शोल्डर और इंपिंजमेंट का पुनर्वास; हफ़्तों तक बगल की गति का रिकॉर्ड।",
  "Elbow stiffness after fracture or immobilisation; general arm strength.": "फ्रैक्चर या प्लास्टर के बाद कोहनी की जकड़न; बाँह की ताक़त।",
  "Hip stability after hip replacement; reduces fall risk in older adults.": "कूल्हा बदलने के बाद कूल्हे की स्थिरता; बुज़ुर्गों में गिरने का जोखिम कम।",
  "Calf strength and ankle mobility after ankle fracture or Achilles injury; balance and fall prevention.": "टखने के फ्रैक्चर या एकिलीज़ चोट के बाद पिंडली की ताक़त और टखने की गति; संतुलन और गिरने से बचाव।",
  "Balance, hip-flexor strength and gait retraining.": "संतुलन, कूल्हे की ताक़त और चलने का अभ्यास।",
  "Leg strength & endurance; CDC fall-risk screen for adults 60+": "पैरों की ताक़त और सहनशक्ति; 60+ उम्र के लिए CDC गिरने के जोखिम की जाँच",
  "Static balance; under 5 s is associated with fall risk": "स्थिर संतुलन; 5 सेकंड से कम होना गिरने के जोखिम से जुड़ा है",
  "Active shoulder flexion vs 180° reference": "कंधे की आगे की सक्रिय गति, 180° संदर्भ से तुलना",
  "Active shoulder abduction vs 180° reference": "कंधे की बगल की सक्रिय गति, 180° संदर्भ से तुलना",
  "Active knee flexion vs 135° reference (post knee-replacement goal is typically 110°+)": "घुटने के मोड़ की सक्रिय गति, 135° संदर्भ से तुलना (घुटना बदलने के बाद लक्ष्य आम तौर पर 110°+)",
  // steps
  "Stand side-on to the laptop, feet hip-width apart, hands forward for balance": "लैपटॉप की ओर बगल से खड़े हों, पैर कूल्हों जितनी दूरी पर, संतुलन के लिए हाथ आगे",
  "Bend knees and push hips back as if sitting on a chair": "घुटने मोड़ें और कूल्हे पीछे ले जाएँ, जैसे कुर्सी पर बैठ रहे हों",
  "Go only as low as is comfortable, then stand tall": "उतना ही नीचे जाएँ जितना आराम से हो, फिर सीधे खड़े हों",
  "Sit on a firm chair, feet flat, arms crossed on chest": "मज़बूत कुर्सी पर बैठें, पैर ज़मीन पर, हाथ छाती पर क्रॉस करके",
  "Lean slightly forward and stand up fully": "थोड़ा आगे झुकें और पूरी तरह खड़े हो जाएँ",
  "Sit back down slowly with control": "धीरे-धीरे, नियंत्रण से वापस बैठें",
  "Sit tall on a chair, side-on to the laptop": "कुर्सी पर सीधे बैठें, लैपटॉप की ओर बगल से",
  "Straighten one knee fully, tighten the thigh, hold 2 seconds": "एक घुटना पूरा सीधा करें, जांघ कसें, 2 सेकंड रोकें",
  "Lower slowly. Repeat, then switch legs": "धीरे से नीचे लाएँ। दोहराएँ, फिर पैर बदलें",
  "Stand side-on to the laptop, arm by your side": "लैपटॉप की ओर बगल से खड़े हों, हाथ शरीर के पास",
  "Raise the arm forward and up, thumb leading, elbow straight": "हाथ को आगे और ऊपर उठाएँ, अँगूठा आगे, कोहनी सीधी",
  "Lift as high as comfortable, then lower slowly": "जितना आराम से हो उतना ऊपर उठाएँ, फिर धीरे से नीचे लाएँ",
  "Face the laptop, arms by your sides": "लैपटॉप की ओर मुँह करके खड़े हों, हाथ शरीर के पास",
  "Raise one arm out to the side, palm forward, elbow straight": "एक हाथ बगल से ऊपर उठाएँ, हथेली आगे, कोहनी सीधी",
  "Keep the shoulder relaxed (no shrugging), lower slowly": "कंधा ढीला रखें (ऊपर न उचकाएँ), धीरे से नीचे लाएँ",
  "Stand or sit side-on to the laptop, upper arm by your side": "लैपटॉप की ओर बगल से खड़े हों या बैठें, बाँह शरीर के पास",
  "Bend the elbow bringing the hand to the shoulder": "कोहनी मोड़कर हाथ को कंधे तक लाएँ",
  "Lower fully. A water bottle works as a light weight": "पूरा नीचे लाएँ। हल्के वज़न के लिए पानी की बोतल ले सकते हैं",
  "Face the laptop holding a chair for balance": "संतुलन के लिए कुर्सी पकड़कर लैपटॉप की ओर मुँह करें",
  "Lift one leg out to the side, toes pointing forward": "एक पैर बगल में उठाएँ, पंजे आगे की ओर",
  "Keep your body upright, lower slowly": "शरीर सीधा रखें, धीरे से नीचे लाएँ",
  "Stand side-on to the laptop, holding a chair for balance": "संतुलन के लिए कुर्सी पकड़कर लैपटॉप की ओर बगल से खड़े हों",
  "Rise onto your toes, lifting both heels as high as is comfortable": "पंजों पर उठें, दोनों एड़ियाँ जितनी आराम से हो उतनी ऊपर",
  "Lower slowly. Precision mode tracks your feet (RTMPose on the NPU)": "धीरे से नीचे आएँ। सटीक मोड आपके पैरों को ट्रैक करता है (NPU पर RTMPose)",
  "Stand side-on to the laptop, holding a chair if needed": "लैपटॉप की ओर बगल से खड़े हों, ज़रूरत हो तो कुर्सी पकड़ें",
  "Lift one knee towards hip height, then lower": "एक घुटना कूल्हे की ऊँचाई तक उठाएँ, फिर नीचे लाएँ",
  "Alternate legs at a steady pace": "एक समान गति से बारी-बारी पैर बदलें",
  "Sit in the middle of a firm chair, side-on to the laptop": "मज़बूत कुर्सी के बीच में बैठें, लैपटॉप की ओर बगल से",
  "Cross your arms over your chest, feet flat": "हाथ छाती पर क्रॉस करें, पैर ज़मीन पर",
  "When the timer starts, stand up fully and sit down, as many times as you can in 30 s": "टाइमर शुरू होते ही पूरी तरह खड़े हों और बैठें, 30 सेकंड में जितनी बार हो सके",
  "Stand facing the laptop near a wall or chair for safety": "सुरक्षा के लिए दीवार या कुर्सी के पास, लैपटॉप की ओर मुँह करके खड़े हों",
  "Cross your arms. Lift one foot off the floor": "हाथ क्रॉस करें। एक पैर ज़मीन से उठाएँ",
  "The timer runs until the foot touches down (max 45 s)": "पैर ज़मीन छूने तक टाइमर चलेगा (अधिकतम 45 सेकंड)",
  "Stand side-on to the laptop": "लैपटॉप की ओर बगल से खड़े हों",
  "Raise both arms forward and up as high as you can": "दोनों हाथ आगे और जितना हो सके उतना ऊपर उठाएँ",
  "Hold at the top for a second; repeat 3 times": "ऊपर एक सेकंड रुकें; 3 बार दोहराएँ",
  "Face the laptop": "लैपटॉप की ओर मुँह करें",
  "Raise both arms out to the sides and up as high as you can": "दोनों हाथ बगल से जितना हो सके उतना ऊपर उठाएँ",
  "Stand side-on holding a chair": "कुर्सी पकड़कर बगल से खड़े हों",
  "Bend one knee, bringing the heel towards your buttock": "एक घुटना मोड़ें, एड़ी को नितंब की ओर लाएँ",
  "Hold for a second; repeat 3 times on each leg": "एक सेकंड रुकें; हर पैर से 3 बार दोहराएँ",
};

export function tr(s) {
  return lang === "hi" && UI_HI[s] ? UI_HI[s] : s;
}
