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
  const want = LANGS[l]?.voice || "en-IN";
  const base = want.split("-")[0];
  return voices.find(v => v.lang === want) || voices.find(v => v.lang?.startsWith(base)) || null;
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
  return s;
}
