"use client"

import { useEffect } from "react"
import { toast } from "@/hooks/useToast"
import { useVaultSocket } from "@/hooks/useVaultSocket"
import type { Source } from "@/lib/types/sources"
import type { Annotation } from "@/lib/types/annotations"

interface VaultToastProps {
  vaultId: string
  currentUserId?: number
}

interface SourceEventData {
  source: Source
  user?: {
    id: number
    username: string
  }
}

interface AnnotationEventData {
  annotation: Annotation
  user?: {
    id: number
    username: string
  }
}

interface MemberEventData {
  user_id: number
  username: string
  role?: "OWNER" | "CONTRIBUTOR" | "VIEWER"
}

/**
 * VaultToast: Displays toast notifications for vault events
 * Listens to WebSocket events and shows context-aware messages
 */
export function VaultToast({ vaultId, currentUserId }: VaultToastProps) {
  const { addEventListener } = useVaultSocket({ vaultId })

  useEffect(() => {
    // Source events
    const cleanupSourceCreated = addEventListener(
      "source.created",
      (data: SourceEventData) => {
        const username = data.user?.username || "Someone"

        // Don't show toast for current user's own actions
        if (data.user?.id === currentUserId) return

        toast({
          title: "New source added",
          description: `${username} added "${data.source.title || data.source.url}"`,
        })
      }
    )

    const cleanupSourceUpdated = addEventListener(
      "source.updated",
      (data: SourceEventData) => {
        const username = data.user?.username || "Someone"

        if (data.user?.id === currentUserId) return

        toast({
          title: "Source updated",
          description: `${username} updated "${data.source.title || data.source.url}"`,
        })
      }
    )

    const cleanupSourceDeleted = addEventListener(
      "source.deleted",
      (data: { source_id: number; user?: { id: number; username: string } }) => {
        const username = data.user?.username || "Someone"

        if (data.user?.id === currentUserId) return

        toast({
          title: "Source removed",
          description: `${username} removed a source`,
        })
      }
    )

    // Annotation events
    const cleanupAnnotationCreated = addEventListener(
      "annotation.created",
      (data: AnnotationEventData) => {
        const username = data.annotation.author?.username || "Someone"

        if (data.annotation.author?.id === currentUserId) return

        toast({
          title: "New annotation",
          description: `${username} added a note`,
        })
      }
    )

    // Member events
    const cleanupMemberAdded = addEventListener(
      "member.added",
      (data: MemberEventData) => {
        toast({
          title: "New collaborator",
          description: `${data.username} joined the vault as ${data.role?.toLowerCase() || "member"}`,
        })
      }
    )

    const cleanupMemberRemoved = addEventListener(
      "member.removed",
      (data: MemberEventData) => {
        toast({
          title: "Collaborator left",
          description: `${data.username} was removed from the vault`,
        })
      }
    )

    const cleanupMemberRoleChanged = addEventListener(
      "member.role_changed",
      (data: MemberEventData & { old_role?: string; new_role?: string }) => {
        toast({
          title: "Role updated",
          description: `${data.username}'s role changed to ${data.new_role?.toLowerCase() || "member"}`,
        })
      }
    )

    // Cleanup all listeners on unmount
    return () => {
      cleanupSourceCreated()
      cleanupSourceUpdated()
      cleanupSourceDeleted()
      cleanupAnnotationCreated()
      cleanupMemberAdded()
      cleanupMemberRemoved()
      cleanupMemberRoleChanged()
    }
  }, [addEventListener, currentUserId])

  // This component doesn't render anything visible
  return null
}
