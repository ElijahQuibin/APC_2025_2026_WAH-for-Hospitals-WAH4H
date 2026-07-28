
import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Search, ShieldAlert, UserCog } from 'lucide-react';
import api from '@/services/api';
import { useToast } from '@/hooks/use-toast';

type UserRole = 'doctor' | 'nurse' | 'lab_technician' | 'pharmacist' | 'billing_clerk' | 'admin';

type ManagedUser = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  name: string;
  role: UserRole;
  status: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  last_login: string | null;
};

const roleOptions: Array<{ value: UserRole; label: string }> = [
  { value: 'doctor', label: 'Doctor' },
  { value: 'nurse', label: 'Nurse' },
  { value: 'lab_technician', label: 'Lab Technician' },
  { value: 'pharmacist', label: 'Pharmacist' },
  { value: 'billing_clerk', label: 'Billing Clerk' },
  { value: 'admin', label: 'Admin' },
];

const UserManagement = () => {
  const { toast } = useToast();
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [editedRoles, setEditedRoles] = useState<Record<number, UserRole>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [savingUserId, setSavingUserId] = useState<number | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/accounts/users/');
      const fetchedUsers = response.data?.data?.users || [];
      setUsers(fetchedUsers);
      setEditedRoles(
        Object.fromEntries(
          fetchedUsers.map((user: ManagedUser) => [user.id, user.role])
        )
      );
      setAccessDenied(false);
    } catch (error: any) {
      if (error?.response?.status === 403) {
        setAccessDenied(true);
      } else {
        toast({
          title: 'Unable to load users',
          description: error?.response?.data?.message || 'Please try again.',
          variant: 'destructive',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const filteredUsers = useMemo(() => {
    return users.filter((user) => {
      const haystack = `${user.name} ${user.email} ${user.username}`.toLowerCase();
      const matchesSearch = haystack.includes(searchTerm.toLowerCase());
      const matchesRole = roleFilter === 'all' || user.role === roleFilter;
      return matchesSearch && matchesRole;
    });
  }, [users, searchTerm, roleFilter]);

  const handleRoleSave = async (userId: number) => {
    const role = editedRoles[userId];
    setSavingUserId(userId);
    try {
      const response = await api.patch(`/api/accounts/users/${userId}/`, { role });
      const updatedUser = response.data?.data?.user as ManagedUser;
      setUsers((prev) => prev.map((user) => (user.id === userId ? updatedUser : user)));
      setEditedRoles((prev) => ({ ...prev, [userId]: updatedUser.role }));
      toast({
        title: 'Role updated',
        description: `${updatedUser.name} is now assigned as ${updatedUser.role}.`,
      });
    } catch (error: any) {
      toast({
        title: 'Role update failed',
        description:
          error?.response?.data?.message ||
          error?.response?.data?.errors?.role?.[0] ||
          'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setSavingUserId(null);
    }
  };

  const formatRole = (role: string) =>
    role
      .split('_')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');

  const formatLastLogin = (value: string | null) => {
    if (!value) return 'Never';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserCog className="w-5 h-5" />
          User Management
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-4 mb-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <Select value={roleFilter} onValueChange={setRoleFilter}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filter by role" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Roles</SelectItem>
              {roleOptions.map((role) => (
                <SelectItem key={role.value} value={role.value}>
                  {role.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={fetchUsers} disabled={isLoading}>
            Refresh
          </Button>
        </div>

        {accessDenied ? (
          <div className="flex items-start gap-3 rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-yellow-900">
            <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-medium">Staff access required</p>
              <p className="text-sm">
                Only Django staff or superuser accounts can manage user roles from this page.
              </p>
            </div>
          </div>
        ) : null}

        {isLoading ? (
          <div className="rounded-lg border p-6 text-sm text-muted-foreground">
            Loading users...
          </div>
        ) : null}

        <div className="border rounded-lg overflow-x-auto no scrollbar">
          <div className="min-w-[980px] grid grid-cols-12 gap-4 p-4 border-b bg-gray-50 font-medium">
            <div className="col-span-3">Name</div>
            <div className="col-span-3">Email</div>
            <div className="col-span-2">Role</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2">Last Login</div>
          </div>

          {!isLoading && filteredUsers.length === 0 ? (
            <div className="p-6 text-sm text-muted-foreground">
              No users matched your search.
            </div>
          ) : null}

          {filteredUsers.map((user) => {
            const selectedRole = editedRoles[user.id] || user.role;
            const isDirty = selectedRole !== user.role;

            return (
              <div
                key={user.id}
                className="min-w-[980px] grid grid-cols-12 gap-4 p-4 border-b items-center"
              >
                <div className="col-span-3">
                  <div className="font-medium">{user.name}</div>
                  <div className="text-xs text-muted-foreground">@{user.username}</div>
                </div>
                <div className="col-span-3 text-muted-foreground max-w-[220px] truncate">
                  {user.email}
                </div>
                <div className="col-span-2 space-y-2">
                  <Select
                    value={selectedRole}
                    onValueChange={(value) =>
                      setEditedRoles((prev) => ({ ...prev, [user.id]: value as UserRole }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {roleOptions.map((role) => (
                        <SelectItem key={role.value} value={role.value}>
                          {role.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    size="sm"
                    variant={isDirty ? 'default' : 'outline'}
                    disabled={!isDirty || savingUserId === user.id}
                    onClick={() => handleRoleSave(user.id)}
                  >
                    {savingUserId === user.id ? 'Saving...' : 'Save Role'}
                  </Button>
                </div>
                <div className="col-span-2 space-y-2">
                  <Badge variant={user.is_active ? 'default' : 'secondary'}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  <div className="text-xs text-muted-foreground">
                    {user.is_staff ? 'Staff' : 'Non-staff'} · {formatRole(user.role)}
                  </div>
                </div>
                <div className="col-span-2 text-sm text-muted-foreground">
                  {formatLastLogin(user.last_login)}
                </div>
              </div>
            );
          })}
        </div>

        <p className="text-xs text-muted-foreground">
          Users with the `admin` role can access the full module set in the main app, in addition to
          Django admin privileges.
        </p>
      </CardContent>
    </Card>
  );
};

export default UserManagement;
