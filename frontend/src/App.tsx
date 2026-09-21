import { FormEvent, useEffect, useEffectEvent, useState } from 'react'
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  BriefcaseBusiness,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleUserRound,
  Clock3,
  FileText,
  Gauge,
  LogOut,
  Mail,
  MapPin,
  Menu,
  Mic2,
  Plus,
  Radio,
  Save,
  Sparkles,
  Square,
  Target,
  Trash2,
  UploadCloud,
  Volume2,
  X,
} from 'lucide-react'
import { api } from './api/client'
import { useVoiceConversation } from './hooks/useVoiceConversation'
import type {
  EvaluationResult,
  InterviewScore,
  ProficiencyLevel,
  Question,
  SkillSelection,
  StartInterviewRequest,
  UserProfile,
  UserProfileUpdate,
} from './types'

const categories = [
  'Software Engineer',
  '.NET Developer',
  'Azure Architect',
  'Full Stack Engineer',
  'Data Engineer',
  'AI Engineer',
  'Engineering Manager',
]
const interviewTypes = ['Technical', 'Behavioral', 'System Design', 'Leadership', 'Mixed']
const companies = ['Generic', 'Microsoft', 'Google', 'Amazon', 'Meta', 'Apple']
const levels: ProficiencyLevel[] = ['Beginner', 'Intermediate', 'Advanced', 'Expert']

const previewQuestions: Question[] = [
  {
    question_id: 'preview-1',
    text: 'You are designing a notification service used by several product teams. How would you keep delivery reliable while allowing each team to choose email, SMS, or push?',
    skill: 'System Design',
    difficulty: 'intermediate',
    type: 'system_design',
    expected_topics: ['delivery guarantees', 'queues', 'channel adapters', 'observability'],
    is_followup: false,
  },
  {
    question_id: 'preview-2',
    text: 'A consumer occasionally processes the same event twice. Walk through how you would diagnose the cause and make processing idempotent.',
    skill: 'Distributed Systems',
    difficulty: 'advanced',
    type: 'technical',
    expected_topics: ['idempotency keys', 'delivery semantics', 'deduplication'],
    is_followup: true,
  },
  {
    question_id: 'preview-3',
    text: 'Implement a function that returns the first time window containing more than a configured number of failed requests. Explain its time and space complexity.',
    skill: 'Algorithms',
    difficulty: 'intermediate',
    type: 'coding',
    expected_topics: ['sliding window', 'edge cases', 'complexity'],
    is_followup: false,
  },
  {
    question_id: 'preview-4',
    text: 'Tell me about a time you disagreed with a technical direction but still had to help the team make progress. What did you do and what changed?',
    skill: 'Collaboration',
    difficulty: 'intermediate',
    type: 'behavioral',
    expected_topics: ['situation', 'action', 'stakeholder alignment', 'result'],
    is_followup: false,
  },
  {
    question_id: 'preview-5',
    text: 'Your public API must serve several enterprise tenants. How would you isolate tenant data, authenticate callers, and investigate suspicious access?',
    skill: 'Security',
    difficulty: 'advanced',
    type: 'technical',
    expected_topics: ['tenant isolation', 'authorization', 'audit logging', 'threat detection'],
    is_followup: false,
  },
  {
    question_id: 'preview-6',
    text: 'A release improves response time but doubles infrastructure cost. How would you decide whether to ship it, and which measurements would support your recommendation?',
    skill: 'Engineering Judgment',
    difficulty: 'advanced',
    type: 'behavioral',
    expected_topics: ['tradeoffs', 'business impact', 'measurement', 'communication'],
    is_followup: false,
  },
]

function App() {
  const [authenticated, setAuthenticated] = useState(api.hasToken())
  const [previewMode, setPreviewMode] = useState(false)
  const [apiOnline, setApiOnline] = useState<boolean | null>(null)

  useEffect(() => {
    fetch('/health')
      .then((response) => setApiOnline(response.ok))
      .catch(() => setApiOnline(false))
  }, [])

  useEffect(() => {
    const handleExpiredSession = () => {
      setAuthenticated(false)
      setPreviewMode(false)
    }
    window.addEventListener('auth-expired', handleExpiredSession)
    return () => window.removeEventListener('auth-expired', handleExpiredSession)
  }, [])

  if (!authenticated && !previewMode) {
    return (
      <AuthScreen
        apiOnline={apiOnline}
        onAuthenticated={() => setAuthenticated(true)}
        onPreview={() => setPreviewMode(true)}
      />
    )
  }

  return (
    <Workspace
      apiOnline={apiOnline}
      previewMode={previewMode}
      onSignOut={() => {
        api.clearToken()
        setAuthenticated(false)
        setPreviewMode(false)
      }}
    />
  )
}

interface AuthScreenProps {
  apiOnline: boolean | null
  onAuthenticated: () => void
  onPreview: () => void
}

function AuthScreen({ apiOnline, onAuthenticated, onPreview }: AuthScreenProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (mode === 'register') await api.register(email, password, fullName)
      const tokens = await api.login(email, password)
      api.saveToken(tokens.access_token)
      onAuthenticated()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to connect to the API.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <div className="brand-lockup">
          <span className="brand-mark"><BrainCircuit size={25} /></span>
          <span>Interview Room</span>
        </div>
        <div className="story-copy">
          <p className="eyebrow">Practice with purpose</p>
          <h1>Your next interview should feel familiar.</h1>
          <p>Adaptive questions, focused feedback, and a quiet place to sharpen how you think out loud.</p>
        </div>
        <div className="story-proof">
          <div><strong>5</strong><span>scoring dimensions</span></div>
          <div><strong>Live</strong><span>difficulty tuning</span></div>
          <div><strong>Clear</strong><span>next steps</span></div>
        </div>
      </section>

      <section className="auth-panel">
        <div className="status-line">
          <span className={`status-dot ${apiOnline === false ? 'offline' : ''}`} />
          {apiOnline === null ? 'Checking local API' : apiOnline ? 'Local API ready' : 'API unavailable'}
        </div>
        <div className="auth-form-wrap">
          <div className="auth-heading">
            <p className="eyebrow">Candidate workspace</p>
            <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
            <p>{mode === 'login' ? 'Continue your interview practice.' : 'Start building a stronger interview signal.'}</p>
          </div>

          <div className="segmented" aria-label="Authentication mode">
            <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Sign in</button>
            <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Register</button>
          </div>

          <form onSubmit={submit}>
            {mode === 'register' && (
              <label>Full name<input value={fullName} onChange={(event) => setFullName(event.target.value)} required /></label>
            )}
            <label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
            <label>Password<input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
            {error && <p className="form-error">{error}</p>}
            <button className="primary-button full" disabled={busy}>
              {busy ? 'Connecting...' : mode === 'login' ? 'Enter workspace' : 'Create account'}
              {!busy && <ArrowRight size={18} />}
            </button>
          </form>

          <div className="divider"><span>or</span></div>
          <button className="text-button preview-button" onClick={onPreview}>
            Preview the workspace <ChevronRight size={17} />
          </button>
        </div>
      </section>
    </main>
  )
}

interface WorkspaceProps {
  apiOnline: boolean | null
  previewMode: boolean
  onSignOut: () => void
}

function Workspace({ apiOnline, previewMode, onSignOut }: WorkspaceProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [view, setView] = useState<'practice' | 'profile'>('practice')
  const [session, setSession] = useState<{
    id: string
    question: Question
    index: number
    total: number
  } | null>(null)
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null)
  const [score, setScore] = useState<InterviewScore | null>(null)

  function goHome() {
    setView('practice')
    setSession(null)
    setEvaluation(null)
    setScore(null)
    setSidebarOpen(false)
  }

  return (
    <div className="app-shell">
      <aside className={sidebarOpen ? 'sidebar open' : 'sidebar'}>
        <button className="brand-lockup compact brand-home" onClick={goHome} aria-label="Go to home">
          <span className="brand-mark"><BrainCircuit size={22} /></span>
          <span>Interview Room</span>
        </button>
        <button className="icon-button close-menu" onClick={() => setSidebarOpen(false)} aria-label="Close menu"><X size={20} /></button>
        <nav>
          <button className={`nav-item ${view === 'practice' ? 'active' : ''}`} onClick={goHome}><Sparkles size={19} /> Practice</button>
          <button className={`nav-item ${view === 'profile' ? 'active' : ''}`} onClick={() => { setView('profile'); setSidebarOpen(false) }}><CircleUserRound size={19} /> Profile</button>
          <button className="nav-item" disabled><BarChart3 size={19} /> Insights <span>Soon</span></button>
        </nav>
        <div className="sidebar-note">
          <Target size={20} />
          <p><strong>Stay specific.</strong> Use examples, tradeoffs, and measurable outcomes.</p>
        </div>
        <button className="nav-item sign-out" onClick={onSignOut}><LogOut size={19} /> {previewMode ? 'Exit preview' : 'Sign out'}</button>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <button className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open menu"><Menu size={21} /></button>
          <div>
            <p className="eyebrow">Practice studio</p>
            <h2>{view === 'profile' ? 'Candidate profile' : score ? 'Session results' : session ? 'Live interview' : 'New session'}</h2>
          </div>
          <div className="topbar-actions">
            {previewMode && <span className="mode-badge">Preview mode</span>}
            <span className="api-status"><span className={`status-dot ${apiOnline === false ? 'offline' : ''}`} />{apiOnline ? 'API ready' : 'Local preview'}</span>
            <button className={`profile-trigger ${view === 'profile' ? 'active' : ''}`} onClick={() => setView('profile')} aria-label="Open profile" title="Open profile"><CircleUserRound size={27} /></button>
          </div>
        </header>

        {view === 'profile' ? (
          <ProfileView previewMode={previewMode} />
        ) : score ? (
          <Results score={score} onRestart={() => { setScore(null); setSession(null); setEvaluation(null) }} />
        ) : session ? (
          <InterviewSession
            session={session}
            previewMode={previewMode}
            evaluation={evaluation}
            onEvaluation={setEvaluation}
            onNext={(next) => { setSession(next); setEvaluation(null) }}
            onComplete={setScore}
          />
        ) : (
          <InterviewSetup
            previewMode={previewMode}
            onStarted={(started) => setSession(started)}
          />
        )}
      </main>
    </div>
  )
}

const previewProfile: UserProfile = {
  id: 'preview-user',
  email: 'alex.morgan@example.com',
  full_name: 'Alex Morgan',
  role: 'candidate',
  is_active: true,
  joined_at: new Date().toISOString(),
  headline: 'Platform engineer preparing for senior technical interviews',
  target_role: 'Azure Architect',
  years_of_experience: 6,
  location: 'Seattle, WA',
  bio: 'I build reliable cloud platforms and enjoy turning ambiguous requirements into clear technical decisions.',
  skills: ['Azure', 'System Design', 'TypeScript', 'Distributed Systems'],
  preferred_company: 'Microsoft',
  preferred_interview_type: 'Mixed',
  total_interviews: 8,
  completed_interviews: 6,
}

function ProfileView({ previewMode }: { previewMode: boolean }) {
  const [profile, setProfile] = useState<UserProfile | null>(previewMode ? previewProfile : null)
  const [skillsText, setSkillsText] = useState(previewMode ? previewProfile.skills.join(', ') : '')
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(!previewMode)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (previewMode) return
    api.getProfile()
      .then((result) => {
        setProfile(result)
        setSkillsText(result.skills.join(', '))
      })
      .catch((requestError) => setMessage(requestError instanceof Error ? requestError.message : 'Unable to load your profile.'))
      .finally(() => setBusy(false))
  }, [previewMode])

  function update<K extends keyof UserProfile>(field: K, value: UserProfile[K]) {
    setProfile((current) => current ? { ...current, [field]: value } : current)
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    if (!profile) return
    setBusy(true)
    setMessage('')
    const payload: UserProfileUpdate = {
      headline: profile.headline,
      target_role: profile.target_role,
      years_of_experience: profile.years_of_experience,
      location: profile.location,
      bio: profile.bio,
      skills: skillsText.split(',').map((skill) => skill.trim()).filter(Boolean),
      preferred_company: profile.preferred_company,
      preferred_interview_type: profile.preferred_interview_type,
    }
    try {
      const saved = previewMode ? { ...profile, ...payload } : await api.updateProfile(payload)
      setProfile(saved)
      setSkillsText(saved.skills.join(', '))
      setEditing(false)
      setMessage(previewMode ? 'Profile changes saved for this preview.' : 'Profile updated.')
    } catch (requestError) {
      setMessage(requestError instanceof Error ? requestError.message : 'Unable to save your profile.')
    } finally {
      setBusy(false)
    }
  }

  if (busy && !profile) return <div className="profile-state">Loading your profile...</div>
  if (!profile) return <div className="profile-state error">{message || 'Profile unavailable.'}</div>

  const initials = profile.full_name.split(/\s+/).map((part) => part[0]).join('').slice(0, 2).toUpperCase()
  return (
    <div className="profile-page">
      <section className="profile-identity">
        <div className="profile-avatar">{initials}</div>
        <div className="profile-intro">
          <p className="eyebrow">Candidate profile</p>
          <h1>{profile.full_name}</h1>
          <p>{profile.headline || 'Add a headline that describes the opportunity you are preparing for.'}</p>
          <div className="identity-meta">
            <span><Mail size={15} />{profile.email}</span>
            <span><MapPin size={15} />{profile.location || 'Location not set'}</span>
            <span><CalendarDays size={15} />Joined {new Date(profile.joined_at).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}</span>
          </div>
        </div>
        <button className="secondary-button" onClick={() => setEditing((value) => !value)}>{editing ? 'Cancel' : 'Edit profile'}</button>
      </section>

      <section className="profile-stats">
        <div><strong>{profile.total_interviews}</strong><span>Interviews started</span></div>
        <div><strong>{profile.completed_interviews}</strong><span>Sessions completed</span></div>
        <div><strong>{profile.years_of_experience}</strong><span>Years of experience</span></div>
        <div><strong>{profile.skills.length}</strong><span>Focus skills</span></div>
      </section>

      <form className="profile-form" onSubmit={save}>
        <section className="profile-section">
          <div className="profile-section-heading"><BriefcaseBusiness size={20} /><div><h2>Professional direction</h2><p>Used to personalize questions and interviewer context.</p></div></div>
          <div className="form-grid two">
            <label>Profile headline<input value={profile.headline} onChange={(event) => update('headline', event.target.value)} disabled={!editing} placeholder="Senior backend engineer" /></label>
            <label>Location<input value={profile.location} onChange={(event) => update('location', event.target.value)} disabled={!editing} placeholder="City, country" /></label>
            <label>Target role<select value={profile.target_role} onChange={(event) => update('target_role', event.target.value)} disabled={!editing}>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Years of experience<input type="number" min="0" max="60" step="0.5" value={profile.years_of_experience} onChange={(event) => update('years_of_experience', Number(event.target.value))} disabled={!editing} /></label>
            <label>Preferred company<select value={profile.preferred_company} onChange={(event) => update('preferred_company', event.target.value)} disabled={!editing}>{companies.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label>Interview focus<select value={profile.preferred_interview_type} onChange={(event) => update('preferred_interview_type', event.target.value)} disabled={!editing}>{interviewTypes.map((item) => <option key={item}>{item}</option>)}</select></label>
          </div>
        </section>

        <section className="profile-section">
          <div className="profile-section-heading"><BrainCircuit size={20} /><div><h2>Experience and strengths</h2><p>Give the interviewer enough context to ask specific questions.</p></div></div>
          <label>Professional bio<textarea value={profile.bio} onChange={(event) => update('bio', event.target.value)} disabled={!editing} maxLength={1000} placeholder="Describe your background, impact, and what you want to practice." /></label>
          <label>Skills <span className="field-hint">Comma separated</span><input value={skillsText} onChange={(event) => setSkillsText(event.target.value)} disabled={!editing} placeholder="Azure, Python, System Design" /></label>
          <div className="profile-skills">{profile.skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
        </section>

        {message && <p className={`profile-message ${message.includes('Unable') ? 'error' : ''}`}>{message}</p>}
        {editing && <div className="profile-actions"><button className="primary-button" disabled={busy}><Save size={17} />{busy ? 'Saving...' : 'Save profile'}</button></div>}
      </form>
    </div>
  )
}

function InterviewSetup({ previewMode, onStarted }: { previewMode: boolean; onStarted: (session: { id: string; question: Question; index: number; total: number }) => void }) {
  const [candidateName, setCandidateName] = useState('')
  const [category, setCategory] = useState(categories[0])
  const [interviewType, setInterviewType] = useState(interviewTypes[0])
  const [company, setCompany] = useState(companies[0])
  const [duration, setDuration] = useState(30)
  const [experience, setExperience] = useState(3)
  const [skills, setSkills] = useState<SkillSelection[]>([
    { name: 'System Design', level: 'Intermediate' },
    { name: 'TypeScript', level: 'Advanced' },
  ])
  const [skillName, setSkillName] = useState('')
  const [skillLevel, setSkillLevel] = useState<ProficiencyLevel>('Intermediate')
  const [resumeId, setResumeId] = useState<string>()
  const [resumeName, setResumeName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function addSkill() {
    const name = skillName.trim()
    if (!name || skills.some((skill) => skill.name.toLowerCase() === name.toLowerCase())) return
    setSkills([...skills, { name, level: skillLevel }])
    setSkillName('')
  }

  async function uploadResume(file?: File) {
    if (!file) return
    setBusy(true)
    setError('')
    try {
      if (previewMode) {
        setResumeName(file.name)
      } else {
        const result = await api.uploadResume(file)
        setResumeId(result.resume_id)
        setResumeName(result.file_name)
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Resume upload failed.')
    } finally {
      setBusy(false)
    }
  }

  async function start(event: FormEvent) {
    event.preventDefault()
    if (!skills.length) {
      setError('Add at least one skill to focus the interview.')
      return
    }
    setBusy(true)
    setError('')
    const payload: StartInterviewRequest = {
      candidate_name: candidateName || 'Candidate',
      resume_id: resumeId,
      target_company: company,
      category,
      interview_type: interviewType,
      duration_minutes: duration,
      years_of_experience: experience,
      skills,
    }
    try {
      if (previewMode) {
        onStarted({ id: 'preview-session', question: previewQuestions[0], index: 1, total: previewQuestions.length })
      } else {
        const result = await api.startInterview(payload)
        onStarted({ id: result.interview_id, question: result.first_question, index: 1, total: result.plan.estimated_questions })
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not start the interview.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="setup-layout">
      <section className="setup-main">
        <div className="section-heading">
          <p className="eyebrow">Shape the room</p>
          <h1>What are you preparing for?</h1>
          <p>We will tune the questions and follow-ups around your target role and experience.</p>
        </div>

        <form className="setup-form" onSubmit={start}>
          <div className="form-section">
            <div className="section-number">01</div>
            <div className="form-section-content">
              <h3>Role and format</h3>
              <div className="form-grid two">
                <label>Your name<input value={candidateName} onChange={(event) => setCandidateName(event.target.value)} placeholder="Alex Morgan" required /></label>
                <label>Target role<select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select></label>
                <label>Interview type<select value={interviewType} onChange={(event) => setInterviewType(event.target.value)}>{interviewTypes.map((item) => <option key={item}>{item}</option>)}</select></label>
                <label>Target company<select value={company} onChange={(event) => setCompany(event.target.value)}>{companies.map((item) => <option key={item}>{item}</option>)}</select></label>
              </div>
              <div className="form-grid two range-row">
                <label>Duration <span>{duration} min</span><input type="range" min="15" max="90" step="15" value={duration} onChange={(event) => setDuration(Number(event.target.value))} /></label>
                <label>Experience <span>{experience} years</span><input type="range" min="0" max="20" value={experience} onChange={(event) => setExperience(Number(event.target.value))} /></label>
              </div>
            </div>
          </div>

          <div className="form-section">
            <div className="section-number">02</div>
            <div className="form-section-content">
              <h3>Skills to test</h3>
              <div className="skill-builder">
                <input value={skillName} onChange={(event) => setSkillName(event.target.value)} placeholder="Add a skill" onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); addSkill() } }} />
                <select value={skillLevel} onChange={(event) => setSkillLevel(event.target.value as ProficiencyLevel)}>{levels.map((item) => <option key={item}>{item}</option>)}</select>
                <button type="button" className="icon-button add-skill" onClick={addSkill} aria-label="Add skill"><Plus size={20} /></button>
              </div>
              <div className="skills-list">
                {skills.map((skill) => (
                  <div className="skill-row" key={skill.name}>
                    <span>{skill.name}</span><small>{skill.level}</small>
                    <button type="button" className="icon-button" onClick={() => setSkills(skills.filter((item) => item.name !== skill.name))} aria-label={`Remove ${skill.name}`}><Trash2 size={16} /></button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="form-section">
            <div className="section-number">03</div>
            <div className="form-section-content">
              <h3>Resume context <span className="optional">Optional</span></h3>
              <label className="upload-zone">
                {resumeName ? <><CheckCircle2 size={24} /><strong>{resumeName}</strong><span>Ready to use</span></> : <><UploadCloud size={26} /><strong>Choose your resume</strong><span>PDF or DOCX</span></>}
                <input type="file" accept=".pdf,.doc,.docx" onChange={(event) => uploadResume(event.target.files?.[0])} />
              </label>
            </div>
          </div>

          {error && <p className="form-error setup-error">{error}</p>}
          <div className="form-actions">
            <p><Clock3 size={17} /> About {Math.max(3, Math.round(duration / 5))} questions</p>
            <button className="primary-button" disabled={busy}>{busy ? 'Preparing...' : 'Start interview'} {!busy && <ArrowRight size={18} />}</button>
          </div>
        </form>
      </section>

      <aside className="prep-rail">
        <div className="prep-visual"><Mic2 size={34} /><span>AI interviewer</span></div>
        <h3>A focused rehearsal, not a quiz.</h3>
        <ul>
          <li><Check size={17} /> Questions adapt to your answers</li>
          <li><Check size={17} /> Feedback across five dimensions</li>
          <li><Check size={17} /> Follow-ups probe depth and clarity</li>
        </ul>
        <div className="quote-block">“Strong answers make the tradeoff visible.”</div>
      </aside>
    </div>
  )
}

interface InterviewSessionProps {
  session: { id: string; question: Question; index: number; total: number }
  previewMode: boolean
  evaluation: EvaluationResult | null
  onEvaluation: (evaluation: EvaluationResult) => void
  onNext: (session: { id: string; question: Question; index: number; total: number }) => void
  onComplete: (score: InterviewScore) => void
}

function InterviewSession({ session, previewMode, evaluation, onEvaluation, onNext, onComplete }: InterviewSessionProps) {
  const [answer, setAnswer] = useState('')
  const [seconds, setSeconds] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [transcript, setTranscript] = useState<Array<{ speaker: 'interviewer' | 'candidate'; text: string }>>([
    { speaker: 'interviewer', text: session.question.text },
  ])
  const voice = useVoiceConversation(previewMode)

  const playCurrentQuestion = useEffectEvent(() => {
    void voice.speak(session.question.text)
  })
  const stopCurrentQuestion = useEffectEvent(() => {
    voice.stopSpeaking()
  })

  useEffect(() => {
    if (evaluation) return
    const timer = window.setInterval(() => setSeconds((value) => value + 1), 1000)
    return () => window.clearInterval(timer)
  }, [evaluation])

  useEffect(() => {
    playCurrentQuestion()
    return () => stopCurrentQuestion()
  }, [session.question.question_id])

  function appendSpokenText(text: string) {
    setAnswer((current) => `${current}${current.trim() ? ' ' : ''}${text}`)
  }

  function toggleListening() {
    if (voice.listening) voice.stopListening()
    else voice.startListening(appendSpokenText)
  }

  async function submit() {
    if (answer.trim().length < 10) {
      setError('Give a little more detail before submitting.')
      return
    }
    setBusy(true)
    setError('')
    voice.stopListening()
    try {
      if (previewMode) {
        onEvaluation({ technical_score: 82, communication_score: 76, confidence_score: 84, problem_solving_score: 79, depth_score: 74, strengths: ['Clear decomposition', 'Good use of delivery guarantees'], missing_points: ['Discuss failure recovery in more detail'], followup_question: session.index === 1 ? previewQuestions[1].text : undefined })
      } else {
        const result = await api.submitAnswer(session.id, session.question.question_id, answer, seconds)
        onEvaluation(result.evaluation)
      }
      setTranscript((turns) => [...turns, { speaker: 'candidate' as const, text: answer.trim() }])
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not submit your answer.')
    } finally {
      setBusy(false)
    }
  }

  async function next() {
    setBusy(true)
    setError('')
    try {
      if (previewMode) {
        if (session.index < previewQuestions.length) {
          setTranscript((turns) => [...turns, { speaker: 'interviewer' as const, text: previewQuestions[session.index].text }])
          onNext({ ...session, index: session.index + 1, question: previewQuestions[session.index] })
          setAnswer('')
          setSeconds(0)
        } else {
          onComplete({ final_rating: 81, grade: 'Strong Hire', breakdown: { technical_score: 82, communication_score: 76, problem_solving_score: 79, confidence_score: 84, depth_score: 74 }, weights: {} })
        }
      } else {
        const question = await api.nextQuestion(session.id)
        if (question) {
          setTranscript((turns) => [...turns, { speaker: 'interviewer' as const, text: question.text }])
          onNext({ ...session, index: session.index + 1, question })
          setAnswer('')
          setSeconds(0)
        } else {
          onComplete(await api.score(session.id))
        }
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not continue the interview.')
    } finally {
      setBusy(false)
    }
  }

  const minutes = String(Math.floor(seconds / 60)).padStart(2, '0')
  const remainingSeconds = String(seconds % 60).padStart(2, '0')

  return (
    <div className="interview-layout">
      <section className="question-stage">
        <div className="session-meta">
          <span>Question {session.index} of {session.total}</span>
          <span className="timer"><Clock3 size={16} /> {minutes}:{remainingSeconds}</span>
        </div>
        <div className="progress-track"><span style={{ width: `${Math.min(100, (session.index / session.total) * 100)}%` }} /></div>
        <div className="question-copy">
          <div className={`virtual-agent ${voice.speaking ? 'speaking' : ''}`}>
            <span className="agent-avatar"><BrainCircuit size={25} /></span>
            <div><strong>Maya</strong><small>{voice.speaking ? 'Speaking now' : voice.listening ? 'Listening to you' : 'AI interviewer'}</small></div>
            <button className="icon-button" onClick={() => voice.speaking ? voice.stopSpeaking() : void voice.speak(session.question.text)} aria-label={voice.speaking ? 'Stop question audio' : 'Replay question'} title={voice.speaking ? 'Stop speaking' : 'Replay question'}>
              {voice.speaking ? <Square size={17} /> : <Volume2 size={19} />}
            </button>
          </div>
          <div className="question-tags"><span>{session.question.skill ?? 'General'}</span><span>{session.question.difficulty}</span>{session.question.is_followup && <span>Follow-up</span>}</div>
          <h1>{session.question.text}</h1>
        </div>
        <div className="answer-mode">
          <div><strong>Answer naturally</strong><span>Speak or type. Your words stay editable before submission.</span></div>
          <button className={`voice-button ${voice.listening ? 'listening' : ''}`} onClick={toggleListening} disabled={Boolean(evaluation) || !voice.recognitionSupported} title={voice.recognitionSupported ? 'Toggle microphone' : 'Voice recognition requires Edge or Chrome'}>
            {voice.listening ? <Square size={17} /> : <Mic2 size={19} />}
            {voice.listening ? 'Stop listening' : 'Answer by voice'}
          </button>
        </div>
        <label className="answer-box">
          <span>Your answer</span>
          <textarea value={answer} onChange={(event) => setAnswer(event.target.value)} disabled={Boolean(evaluation)} placeholder="Think out loud. Explain your choices, assumptions, and tradeoffs..." />
          <small>{answer.trim() ? answer.trim().split(/\s+/).length : 0} words</small>
        </label>
        {voice.listening && <div className="live-transcript"><Radio size={15} /><span>{voice.interimTranscript || 'Listening for your answer...'}</span></div>}
        {error && <p className="form-error">{error}</p>}
        {!evaluation && <button className="primary-button submit-answer" onClick={submit} disabled={busy}>{busy ? 'Evaluating...' : 'Submit answer'} <ArrowRight size={18} /></button>}
        <details className="transcript-panel">
          <summary><FileText size={17} /> Conversation transcript <span>{transcript.length} turns</span></summary>
          <div className="transcript-turns">
            {transcript.map((turn, index) => (
              <div className={`transcript-turn ${turn.speaker}`} key={`${turn.speaker}-${index}`}>
                <span>{turn.speaker === 'interviewer' ? 'Maya' : 'You'}</span>
                <p>{turn.text}</p>
              </div>
            ))}
          </div>
        </details>
      </section>

      <aside className="feedback-rail">
        {evaluation ? (
          <>
            <div className="feedback-heading"><span className="feedback-icon"><Gauge size={23} /></span><div><p className="eyebrow">Answer signal</p><h3>Focused feedback</h3></div></div>
            <div className="score-list">
              {Object.entries({ Technical: evaluation.technical_score, Communication: evaluation.communication_score, Confidence: evaluation.confidence_score, 'Problem solving': evaluation.problem_solving_score, Depth: evaluation.depth_score }).map(([label, value]) => (
                <div className="score-row" key={label}><span>{label}</span><strong>{Math.round(value)}</strong><div><i style={{ width: `${value}%` }} /></div></div>
              ))}
            </div>
            <div className="feedback-points good"><strong>What landed</strong>{evaluation.strengths.map((item) => <p key={item}><Check size={15} />{item}</p>)}</div>
            <div className="feedback-points improve"><strong>Push further</strong>{evaluation.missing_points.map((item) => <p key={item}><ArrowRight size={15} />{item}</p>)}</div>
            <button className="primary-button full" onClick={next} disabled={busy}>{session.index >= session.total ? 'See final score' : 'Next question'} <ChevronRight size={18} /></button>
          </>
        ) : (
          <div className="thinking-guide">
            <BrainCircuit size={32} />
            <p className="eyebrow">Answer framework</p>
            <h3>Make your reasoning easy to follow.</h3>
            <ol><li>Clarify the goal</li><li>State your assumptions</li><li>Compare tradeoffs</li><li>Close with impact</li></ol>
          </div>
        )}
      </aside>
    </div>
  )
}

function Results({ score, onRestart }: { score: InterviewScore; onRestart: () => void }) {
  const labels: Record<string, string> = { technical_score: 'Technical', communication_score: 'Communication', problem_solving_score: 'Problem solving', confidence_score: 'Confidence', depth_score: 'Depth' }
  return (
    <div className="results-layout">
      <section className="result-hero">
        <div className="result-ring"><strong>{Math.round(score.final_rating)}</strong><span>/ 100</span></div>
        <div><p className="eyebrow">Interview complete</p><h1>{score.grade}</h1><p>Your signal is strongest when you connect technical choices to their practical impact.</p></div>
      </section>
      <section className="breakdown">
        <div className="section-heading"><p className="eyebrow">Performance profile</p><h2>Where your answer showed strength</h2></div>
        <div className="breakdown-grid">
          {Object.entries(score.breakdown).map(([key, value]) => <div className="metric" key={key}><span>{labels[key] ?? key}</span><strong>{Math.round(value)}</strong><div><i style={{ width: `${value}%` }} /></div></div>)}
        </div>
      </section>
      <button className="primary-button" onClick={onRestart}><Plus size={18} /> Start another session</button>
    </div>
  )
}

export default App