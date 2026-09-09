import i18n from "i18next"
import { initReactI18next } from "react-i18next"
import en from "./locales/en.json"
import de from "./locales/de.json"
import ur from "./locales/ur.json"
import zh from "./locales/zh.json"

export type Language = "en" | "de" | "ur" | "zh"

export const LANGUAGES: { code: Language; label: string; nativeLabel: string; dir: "ltr" | "rtl" }[] = [
  { code: "en", label: "English",  nativeLabel: "English", dir: "ltr" },
  { code: "de", label: "German",   nativeLabel: "Deutsch (Österreich)", dir: "ltr" },
  { code: "ur", label: "Urdu",     nativeLabel: "اردو",    dir: "rtl" },
  { code: "zh", label: "Chinese",  nativeLabel: "中文",     dir: "ltr" },
]

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    de: { translation: de },
    ur: { translation: ur },
    zh: { translation: zh },
  },
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
})

export default i18n
