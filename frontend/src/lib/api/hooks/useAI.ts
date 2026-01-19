// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * TanStack Query hooks for AI Agents API.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';

const API_BASE = '/ai';

export interface AIModelProvider {
    id: string;
    provider_type: string;
    display_name: string;
    model_name: string;
    is_active: boolean;
    is_default: boolean;
    key_configured: boolean;
    endpoint_url?: string;
    max_tokens: number;
    temperature: number;
}

export interface AIConversation {
    id: string;
    agent_type: string;
    title: string;
    created_at: string;
    message_count: number;
}

export interface AIMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    requires_action?: boolean;
}

export interface AIConversationResponse {
    conversation_id: string;
    message_id: string;
    response: string;
    requires_action: boolean;
    error?: string;
}

export interface AIAgentTask {
    id: string;
    agent_type: string;
    agent_type_display?: string;
    title: string;
    description: string;
    task_type: string;
    input_data: Record<string, unknown>;
    output_data: Record<string, unknown>;
    status: 'pending' | 'in_progress' | 'awaiting_approval' | 'revision_requested' | 'approved' | 'rejected' | 'executing' | 'completed' | 'failed';
    created_at: string;
    updated_at?: string;
    correlation_id: string;
    initiated_by?: {
        username: string;
        email: string;
        name: string;
    };
    approved_by?: {
        username: string;
        email: string;
        name: string;
    };
}

export interface AIAgentStats {
    active_tasks: number;
    awaiting_approval: number;
    completed_today: number;
    tokens_used: number;
}

// List AI model providers
export function useModelProviders() {
    return useQuery<{ providers: AIModelProvider[] }>({
        queryKey: ['ai', 'providers'],
        queryFn: async () => {
            return await api.get(`${API_BASE}/providers/`);
        },
    });
}

// Configure AI model provider
export function useConfigureProvider() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (data: {
            provider_type: string;
            api_key: string;
            model_name: string;
            display_name?: string;
            endpoint_url?: string;
            max_tokens?: number;
            temperature?: number;
            is_default?: boolean;
        }) => {
            return await api.post(`${API_BASE}/providers/configure/`, data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai', 'providers'] });
        },
    });
}

// Delete AI model provider by ID
export function useDeleteProvider() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (providerId: string) => {
            return await api.delete(`${API_BASE}/providers/${providerId}/delete/`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai', 'providers'] });
        },
    });
}

// Delete all providers of a specific type
export function useDeleteProviderByType() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (providerType: string) => {
            return await api.delete(`${API_BASE}/providers/type/${providerType}/delete/`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai', 'providers'] });
        },
    });
}

// Ask Amani
export function useAmaniChat() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (data: {
            message: string;
            conversation_id?: string;
            context?: Record<string, unknown>;
        }) => {
            return await api.post(`${API_BASE}/amani/ask/`, data) as AIConversationResponse;
        },
        onSuccess: (data) => {
            // Invalidate conversation queries
            queryClient.invalidateQueries({ queryKey: ['ai', 'conversations'] });
            if (data.conversation_id) {
                queryClient.invalidateQueries({ queryKey: ['ai', 'conversation', data.conversation_id] });
            }
        },
    });
}

// Get conversation history
export function useConversation(conversationId: string | null) {
    return useQuery<{ conversation_id: string; messages: AIMessage[] }>({
        queryKey: ['ai', 'conversation', conversationId],
        queryFn: async () => {
            if (!conversationId) throw new Error('Conversation ID required');
            return await api.get(`${API_BASE}/conversations/${conversationId}/`);
        },
        enabled: !!conversationId,
    });
}

// List conversations
export function useConversations(agentType?: string) {
    return useQuery<{ conversations: AIConversation[] }>({
        queryKey: ['ai', 'conversations', agentType],
        queryFn: async () => {
            const params = agentType ? `?agent_type=${agentType}` : '';
            return await api.get(`${API_BASE}/conversations/${params}`);
        },
    });
}

// Get AI agent stats
export function useAIAgentStats() {
    return useQuery<AIAgentStats>({
        queryKey: ['ai', 'stats'],
        queryFn: async () => {
            return await api.get(`${API_BASE}/stats/`);
        },
    });
}

// List AI agent tasks
export function useAIAgentTasks(status?: string) {
    return useQuery<{ tasks: AIAgentTask[] }>({
        queryKey: ['ai', 'tasks', status],
        queryFn: async () => {
            const params = status ? `?status=${status}` : '';
            return await api.get(`${API_BASE}/tasks/${params}`);
        },
    });
}

// List pending approvals
export function usePendingApprovals() {
    return useQuery<{ pending_approvals: AIAgentTask[]; total_count: number }>({
        queryKey: ['ai', 'pending-approvals'],
        queryFn: async () => {
            return await api.get(`${API_BASE}/tasks/pending/`);
        },
        refetchInterval: 180000, // Refresh every 3 minutes
    });
}

// Get a single task
export function useAIAgentTask(taskId: string | null) {
    return useQuery<{ task: AIAgentTask }>({
        queryKey: ['ai', 'task', taskId],
        queryFn: async () => {
            if (!taskId) throw new Error('Task ID required');
            return await api.get(`${API_BASE}/tasks/${taskId}/`);
        },
        enabled: !!taskId,
    });
}

// Approve task
export function useApproveTask() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async ({ taskId, comment }: { taskId: string; comment?: string }) => {
            return await api.post(`${API_BASE}/tasks/${taskId}/approve/`, { comment });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ai', 'pending-approvals'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'tasks'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'task', variables.taskId] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'stats'] });
        },
    });
}

// Reject task
export function useRejectTask() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async ({ taskId, reason }: { taskId: string; reason: string }) => {
            return await api.post(`${API_BASE}/tasks/${taskId}/reject/`, { reason });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ai', 'pending-approvals'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'tasks'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'task', variables.taskId] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'stats'] });
        },
    });
}

// Request revision/feedback for a task
export interface RevisionResponse {
    success: boolean;
    message: string;
    task: {
        id: string;
        status: string;
        title?: string;
        description?: string;
        revision_number: number;
        original_recommendation?: string;
        revised_recommendation?: string;
        feedback: string;
        ai_status?: string;
    };
}

export function useRequestRevision() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async ({ taskId, feedback }: { taskId: string; feedback: string }): Promise<RevisionResponse> => {
            return await api.post(`${API_BASE}/tasks/${taskId}/request-revision/`, { feedback });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ai', 'pending-approvals'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'tasks'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'task', variables.taskId] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'stats'] });
        },
    });
}

// Create task from message (for AI recommendations needing approval)
export interface CreateTaskResponse {
    task: AIAgentTask;
    message?: string;
}

export function useCreateTaskFromMessage() {
    const queryClient = useQueryClient();
    
    return useMutation<CreateTaskResponse, Error, {
        title: string;
        description: string;
        agent_type?: string;
        task_type?: string;
        input_data?: Record<string, unknown>;
        output_data?: Record<string, unknown>;
        conversation_id?: string;
    }>({
        mutationFn: async (data) => {
            return await api.post<CreateTaskResponse>(`${API_BASE}/tasks/create/`, data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai', 'pending-approvals'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'tasks'] });
            queryClient.invalidateQueries({ queryKey: ['ai', 'stats'] });
        },
    });
}

// Send message helper (for use in components)
export function useSendMessage() {
    const { mutateAsync: askAmani } = useAmaniChat();
    
    return {
        sendMessage: async (message: string, conversationId?: string, context?: Record<string, unknown>) => {
            return await askAmani({ message, conversation_id: conversationId, context });
        },
    };
}

