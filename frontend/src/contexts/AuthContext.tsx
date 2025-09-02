import React, { createContext, useContext, useState, useEffect } from 'react'
import { getCurrentUser, signIn, signOut, signUp, fetchAuthSession } from 'aws-amplify/auth'
import { useNavigate } from 'react-router-dom'

interface User {
  id: string
  email: string
  username: string
  hasCompletedOnboarding?: boolean
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, username: string) => Promise<void>
  logout: () => Promise<void>
  getAccessToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const currentUser = await getCurrentUser()
      const session = await fetchAuthSession()
      
      if (currentUser && session.tokens?.accessToken) {
        const response = await fetch('/api/v1/profile', {
          headers: {
            Authorization: `Bearer ${session.tokens.accessToken}`,
          },
        })
        
        if (response.ok) {
          const profileData = await response.json()
          setUser({
            id: currentUser.userId,
            email: currentUser.signInDetails?.loginId || '',
            username: currentUser.username || '',
            hasCompletedOnboarding: profileData.has_completed_onboarding,
          })
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const { isSignedIn } = await signIn({ username: email, password })
      
      if (isSignedIn) {
        await checkAuth()
        navigate('/dashboard')
      }
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (email: string, password: string, username: string) => {
    try {
      const { isSignUpComplete, userId } = await signUp({
        username: email,
        password,
        options: {
          userAttributes: {
            email,
            preferred_username: username,
          },
        },
      })

      if (isSignUpComplete) {
        await login(email, password)
      }
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await signOut()
      setUser(null)
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const getAccessToken = async (): Promise<string | null> => {
    try {
      const session = await fetchAuthSession()
      return session.tokens?.accessToken?.toString() || null
    } catch (error) {
      console.error('Failed to get access token:', error)
      return null
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}