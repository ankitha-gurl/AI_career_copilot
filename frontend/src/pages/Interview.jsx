import { useState } from 'react'
import api from '../api/client'

export default function Interview() {
  const [targetRole, setTargetRole] = useState('')
  const [numQuestions, setNumQuestions] = useState(5)
  const [generating, setGenerating] = useState(false)
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})
  const [evaluations, setEvaluations] = useState({})
  const [evaluatingId, setEvaluatingId] = useState(null)
  const [error, setError] = useState('')

  async function handleGenerate(e) {
    e.preventDefault()
    if (!targetRole.trim()) return
    setGenerating(true)
    setError('')
    setQuestions([])
    setEvaluations({})
    try {
      const res = await api.post('/interview/questions', { target_role: targetRole, num_questions: Number(numQuestions) })
      setQuestions(res.data.questions)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not generate interview questions.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleEvaluate(questionId) {
    const answer = answers[questionId]
    if (!answer?.trim()) return
    setEvaluatingId(questionId)
    try {
      const res = await api.post('/interview/evaluate', { question_id: questionId, user_answer: answer })
      setEvaluations((prev) => ({ ...prev, [questionId]: res.data.evaluation }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not evaluate answer.')
    } finally {
      setEvaluatingId(null)
    }
  }

  return (
    <div className="page">
      <h1>Interview Preparation</h1>
      <p className="page-subtitle">Generate role-specific interview questions, answer them, and get AI feedback.</p>

      {error && <div className="alert-error">{error}</div>}

      <form className="form-card inline-form" onSubmit={handleGenerate}>
        <input placeholder="Target role, e.g. Backend Engineer" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
        <input type="number" min={1} max={12} value={numQuestions} onChange={(e) => setNumQuestions(e.target.value)} style={{ width: 80 }} />
        <button type="submit" disabled={generating}>{generating ? 'Generating...' : 'Generate Questions'}</button>
      </form>

      {questions.map((q) => (
        <div key={q.id} className="interview-card">
          <span className="badge">{q.question_type}</span>
          <h3>{q.question_text}</h3>
          {q.expected_concepts && <p className="muted">Expected concepts: {q.expected_concepts}</p>}

          <textarea
            rows={3}
            placeholder="Type your answer here..."
            value={answers[q.id] || ''}
            onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
          />
          <button onClick={() => handleEvaluate(q.id)} disabled={evaluatingId === q.id}>
            {evaluatingId === q.id ? 'Evaluating...' : 'Submit Answer for Feedback'}
          </button>

          {evaluations[q.id] && (
            <div className="evaluation-box">
              <strong>Score: {evaluations[q.id].score}/100</strong>
              <p>{evaluations[q.id].overall_feedback}</p>
              <p className="muted">Missing: {(evaluations[q.id].missing_points || []).join(', ') || 'None'}</p>
            </div>
          )}

          <details>
            <summary>Show model answer</summary>
            <p>{q.model_answer}</p>
            <p className="muted">{q.explanation}</p>
          </details>
        </div>
      ))}
    </div>
  )
}
