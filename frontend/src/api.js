import axios from 'axios'

const BASE_URL = 'https://parcelpilot-support-agent-ncj8.onrender.com'

export const login = async (username, password) => {
  const res = await axios.post(`${BASE_URL}/auth/login`, { username, password })
  return res.data
}

export const sendCustomerMessage = async (message, history, token) => {
  const res = await axios.post(
    `${BASE_URL}/chat/customer`,
    { message, history },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export const sendInternalMessage = async (message, history, token) => {
  const res = await axios.post(
    `${BASE_URL}/chat/internal`,
    { message, history },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}

export const confirmEscalation = async (ref_id, ref_type, reason, token) => {
  const res = await axios.post(
    `${BASE_URL}/escalation/confirm`,
    { ref_id, ref_type, reason },
    { headers: { Authorization: `Bearer ${token}` } }
  )
  return res.data
}