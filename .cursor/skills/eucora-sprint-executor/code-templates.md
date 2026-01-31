# Code Templates

Ready-to-use code templates for Phase 2 enhancements.

---

## Django Model Template

```python
"""
apps/{app_name}/models.py
"""
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel, CorrelationIdModel


class YourModel(TimeStampedModel, CorrelationIdModel):
    """
    Description of what this model represents.

    Attributes:
        name: The name of the entity
        description: Optional description
        is_active: Whether this entity is active
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Foreign Keys
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_%(class)ss'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Your Model'
        verbose_name_plural = 'Your Models'

    def __str__(self) -> str:
        return self.name
```

---

## Django Serializer Template

```python
"""
apps/{app_name}/serializers.py
"""
from rest_framework import serializers
from .models import YourModel


class YourModelSerializer(serializers.ModelSerializer):
    """Serializer for YourModel."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = YourModel
        fields = [
            'id',
            'name',
            'description',
            'is_active',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'correlation_id',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'correlation_id']


class YourModelCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating YourModel."""

    class Meta:
        model = YourModel
        fields = ['name', 'description', 'is_active']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
```

---

## Django ViewSet Template with RBAC

```python
"""
apps/{app_name}/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.rbac.mixins import RBACViewSetMixin
from apps.rbac.decorators import require_permission

from .models import YourModel
from .serializers import YourModelSerializer, YourModelCreateSerializer


class YourModelViewSet(RBACViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for YourModel CRUD operations.

    list: List all models (requires resource:read)
    create: Create a new model (requires resource:create)
    retrieve: Get a specific model (requires resource:read)
    update: Update a model (requires resource:update)
    destroy: Delete a model (requires resource:delete)
    """
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
    permission_required = 'resource:read'

    # RBAC permission mapping per action
    permission_map = {
        'list': 'resource:read',
        'retrieve': 'resource:read',
        'create': 'resource:create',
        'update': 'resource:update',
        'partial_update': 'resource:update',
        'destroy': 'resource:delete',
    }

    def get_serializer_class(self):
        if self.action == 'create':
            return YourModelCreateSerializer
        return YourModelSerializer

    def get_queryset(self):
        """Filter by correlation_id if provided."""
        queryset = super().get_queryset()
        correlation_id = self.request.query_params.get('correlation_id')
        if correlation_id:
            queryset = queryset.filter(correlation_id=correlation_id)
        return queryset

    @action(detail=True, methods=['post'])
    @require_permission('resource:special_action')
    def special_action(self, request, pk=None):
        """Custom action requiring specific permission."""
        obj = self.get_object()
        # Perform action
        return Response({'status': 'success'})
```

---

## Django URL Pattern Template

```python
"""
apps/{app_name}/urls.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'your-models', views.YourModelViewSet, basename='your-model')

app_name = '{app_name}'

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## Django Test Template

```python
"""
apps/{app_name}/tests/test_api.py
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.rbac.models import Role, Permission, UserRole
from ..models import YourModel


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='testpass123'  # pragma: allowlist secret
    )
    # Assign admin role with all permissions
    role = Role.objects.get(name='platform_admin')
    UserRole.objects.create(user=user, role=role)
    return user


@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def sample_model(db, admin_user):
    return YourModel.objects.create(
        name='Test Model',
        description='Test description',
        created_by=admin_user
    )


class TestYourModelAPI:
    """Test cases for YourModel API."""

    def test_list_models(self, authenticated_client, sample_model):
        """Test listing all models."""
        url = reverse('your-model-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_model(self, authenticated_client):
        """Test creating a new model."""
        url = reverse('your-model-list')
        data = {
            'name': 'New Model',
            'description': 'New description'
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Model'

    def test_retrieve_model(self, authenticated_client, sample_model):
        """Test retrieving a specific model."""
        url = reverse('your-model-detail', args=[sample_model.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == sample_model.id

    def test_update_model(self, authenticated_client, sample_model):
        """Test updating a model."""
        url = reverse('your-model-detail', args=[sample_model.id])
        data = {'name': 'Updated Name'}
        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_delete_model(self, authenticated_client, sample_model):
        """Test deleting a model."""
        url = reverse('your-model-detail', args=[sample_model.id])
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_unauthenticated_access(self, api_client):
        """Test that unauthenticated access is denied."""
        url = reverse('your-model-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCorrelationIdIsolation:
    """Test correlation ID isolation (MANDATORY per AGENTS.md)."""

    def test_filter_by_correlation_id(self, authenticated_client, sample_model):
        """Test filtering by correlation_id."""
        url = reverse('your-model-list')
        response = authenticated_client.get(
            url,
            {'correlation_id': str(sample_model.correlation_id)}
        )

        assert response.status_code == status.HTTP_200_OK
        for item in response.data:
            assert item['correlation_id'] == str(sample_model.correlation_id)
```

---

## TypeScript Types Template

```typescript
/**
 * frontend/src/types/{feature}.ts
 */

export interface YourModel {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
  createdBy: string;
  createdByName: string;
  createdAt: string;
  updatedAt: string;
  correlationId: string;
}

export interface YourModelCreate {
  name: string;
  description?: string;
  isActive?: boolean;
}

export interface YourModelUpdate {
  name?: string;
  description?: string;
  isActive?: boolean;
}

export interface YourModelFilters {
  search?: string;
  isActive?: boolean;
  createdBy?: string;
}

export type YourModelSortField = 'name' | 'createdAt' | 'updatedAt';
export type SortDirection = 'asc' | 'desc';

export interface YourModelListParams {
  page?: number;
  pageSize?: number;
  filters?: YourModelFilters;
  sortBy?: YourModelSortField;
  sortDirection?: SortDirection;
}
```

---

## React Hook Template

```typescript
/**
 * frontend/src/lib/api/hooks/use{Feature}.ts
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  YourModel,
  YourModelCreate,
  YourModelUpdate,
  YourModelListParams,
} from '@/types/{feature}';

const QUERY_KEY = 'your-models';

export function useYourModels(params?: YourModelListParams) {
  return useQuery({
    queryKey: [QUERY_KEY, params],
    queryFn: async () => {
      const response = await api.get<YourModel[]>('/api/your-models/', {
        params,
      });
      return response.data;
    },
  });
}

export function useYourModel(id: string) {
  return useQuery({
    queryKey: [QUERY_KEY, id],
    queryFn: async () => {
      const response = await api.get<YourModel>(`/api/your-models/${id}/`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateYourModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: YourModelCreate) => {
      const response = await api.post<YourModel>('/api/your-models/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
  });
}

export function useUpdateYourModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: YourModelUpdate }) => {
      const response = await api.patch<YourModel>(
        `/api/your-models/${id}/`,
        data
      );
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, id] });
    },
  });
}

export function useDeleteYourModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/your-models/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
    },
  });
}
```

---

## React Component Template

```tsx
/**
 * frontend/src/components/{Feature}/{Feature}Card.tsx
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MoreHorizontal, Edit, Trash2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { YourModel } from '@/types/{feature}';

interface YourModelCardProps {
  model: YourModel;
  onEdit: (model: YourModel) => void;
  onDelete: (model: YourModel) => void;
}

export function YourModelCard({ model, onEdit, onDelete }: YourModelCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{model.name}</CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant={model.isActive ? 'default' : 'secondary'}>
            {model.isActive ? 'Active' : 'Inactive'}
          </Badge>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(model)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDelete(model)}
                className="text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{model.description}</p>
        <div className="mt-2 text-xs text-muted-foreground">
          Created by {model.createdByName} on{' '}
          {new Date(model.createdAt).toLocaleDateString()}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## React Page Template with RBAC

```tsx
/**
 * frontend/src/routes/{feature}/{Feature}Page.tsx
 */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { useYourModels, useDeleteYourModel } from '@/lib/api/hooks/use{Feature}';
import { YourModelCard } from '@/components/{Feature}/{Feature}Card';
import { CreateDialog } from '@/components/{Feature}/CreateDialog';
import { EditDialog } from '@/components/{Feature}/EditDialog';
import { PermissionGate } from '@/components/auth/PermissionGate';
import { useToast } from '@/hooks/use-toast';
import type { YourModel } from '@/types/{feature}';

export default function YourModelPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [editModel, setEditModel] = useState<YourModel | null>(null);

  const { data: models, isLoading } = useYourModels();
  const deleteModel = useDeleteYourModel();
  const { toast } = useToast();

  const handleDelete = async (model: YourModel) => {
    try {
      await deleteModel.mutateAsync(model.id);
      toast({
        title: 'Deleted',
        description: `${model.name} has been deleted.`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete model.',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Your Models</h1>
        <PermissionGate permission="resource:create">
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create New
          </Button>
        </PermissionGate>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {models?.map((model) => (
          <YourModelCard
            key={model.id}
            model={model}
            onEdit={setEditModel}
            onDelete={handleDelete}
          />
        ))}
      </div>

      <CreateDialog open={createOpen} onOpenChange={setCreateOpen} />

      {editModel && (
        <EditDialog
          model={editModel}
          open={!!editModel}
          onOpenChange={(open) => !open && setEditModel(null)}
        />
      )}
    </div>
  );
}
```
