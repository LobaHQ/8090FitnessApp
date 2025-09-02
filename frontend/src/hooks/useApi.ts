import { useState, useCallback } from 'react'
import axios, { AxiosRequestConfig, AxiosError } from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from './use-toast'

interface ApiResponse<T> {
  data: T | null
  error: string | null
  loading: boolean
}

export function useApi<T = any>() {
  const [state, setState] = useState<ApiResponse<T>>({
    data: null,
    error: null,
    loading: false,
  })
  const { getAccessToken } = useAuth()
  const { toast } = useToast()

  const execute = useCallback(
    async (url: string, config?: AxiosRequestConfig) => {
      setState({ data: null, error: null, loading: true })

      try {
        const token = await getAccessToken()
        
        const response = await axios({
          url,
          ...config,
          headers: {
            ...config?.headers,
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        })

        setState({ data: response.data, error: null, loading: false })
        return response.data
      } catch (error) {
        const axiosError = error as AxiosError<{ detail: string }>
        const errorMessage = axiosError.response?.data?.detail || 'An error occurred'
        
        setState({ data: null, error: errorMessage, loading: false })
        
        toast({
          title: 'Error',
          description: errorMessage,
          variant: 'destructive',
        })
        
        throw error
      }
    },
    [getAccessToken, toast]
  )

  return { ...state, execute }
}