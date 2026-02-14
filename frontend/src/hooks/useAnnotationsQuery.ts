import { useQuery } from '@tanstack/react-query'
import { getAnnotations } from '@/lib/api/annotations'
import type { Annotation } from '@/lib/types/annotations'

interface UseAnnotationsQueryOptions {
  sourceId: number
}

/**
 * React Query hook to fetch annotations for a source
 * Includes nested replies in the response
 * Shorter stale time (10s) for real-time collaboration
 */
export function useAnnotationsQuery({ sourceId }: UseAnnotationsQueryOptions) {
  return useQuery<Annotation[]>({
    queryKey: ['annotations', sourceId],
    queryFn: () => getAnnotations(sourceId),
    enabled: !!sourceId,
    staleTime: 10 * 1000, // 10 seconds - shorter for collaboration
  })
}
