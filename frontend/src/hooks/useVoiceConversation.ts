import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

interface RecognitionResultEvent extends Event {
  resultIndex: number
  results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }>
}

interface RecognitionLike {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: RecognitionResultEvent) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

type RecognitionConstructor = new () => RecognitionLike

declare global {
  interface Window {
    SpeechRecognition?: RecognitionConstructor
    webkitSpeechRecognition?: RecognitionConstructor
  }
}

export function useVoiceConversation(previewMode: boolean) {
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const recognitionRef = useRef<RecognitionLike | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const recognitionSupported = Boolean(window.SpeechRecognition ?? window.webkitSpeechRecognition)

  useEffect(() => () => {
    recognitionRef.current?.stop()
    audioRef.current?.pause()
    window.speechSynthesis?.cancel()
  }, [])

  function startListening(onFinalTranscript: (text: string) => void) {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!Recognition) return

    const recognition = new Recognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index]
        if (result.isFinal) final += result[0].transcript
        else interim += result[0].transcript
      }
      setInterimTranscript(interim)
      if (final.trim()) onFinalTranscript(final.trim())
    }
    recognition.onerror = () => setListening(false)
    recognition.onend = () => {
      setListening(false)
      setInterimTranscript('')
    }
    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  function stopListening() {
    recognitionRef.current?.stop()
    recognitionRef.current = null
    setListening(false)
    setInterimTranscript('')
  }

  function speakWithBrowser(text: string) {
    return new Promise<void>((resolve) => {
      if (!window.speechSynthesis) {
        resolve()
        return
      }
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.94
      utterance.pitch = 0.96
      utterance.onstart = () => setSpeaking(true)
      utterance.onend = () => { setSpeaking(false); resolve() }
      utterance.onerror = () => { setSpeaking(false); resolve() }
      window.speechSynthesis.speak(utterance)
    })
  }

  async function speak(text: string) {
    stopSpeaking()
    if (previewMode) {
      await speakWithBrowser(text)
      return
    }
    try {
      setSpeaking(true)
      const audio = new Audio(URL.createObjectURL(await api.synthesizeSpeech(text)))
      audioRef.current = audio
      audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(audio.src) }
      audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(audio.src) }
      await audio.play()
    } catch {
      setSpeaking(false)
      await speakWithBrowser(text)
    }
  }

  function stopSpeaking() {
    audioRef.current?.pause()
    audioRef.current = null
    window.speechSynthesis?.cancel()
    setSpeaking(false)
  }

  return { listening, speaking, interimTranscript, recognitionSupported, startListening, stopListening, speak, stopSpeaking }
}