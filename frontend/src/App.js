import React, { useState, useEffect } from 'react';
import './App.css';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { 
  Truck, Package, Users, Bell, Search, Plus, Edit, Trash2, CheckCircle, 
  Clock, MapPin, User, Shield, Warehouse, Menu, X, Building, 
  DollarSign, FileText, Grid3X3, Package2, Home
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState('cargo');
  const [activeSection, setActiveSection] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [cargo, setCargo] = useState([]);
  const [users, setUsers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [warehouseCargo, setWarehouseCargo] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [trackingNumber, setTrackingNumber] = useState('');
  const [trackingResult, setTrackingResult] = useState(null);

  // Form states
  const [loginForm, setLoginForm] = useState({ phone: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ full_name: '', phone: '', password: '', role: 'user' });
  const [cargoForm, setCargoForm] = useState({
    recipient_name: '',
    recipient_phone: '',
    route: 'moscow_to_tajikistan',
    weight: '',
    description: '',
    declared_value: '',
    sender_address: '',
    recipient_address: ''
  });
  const [warehouseForm, setWarehouseForm] = useState({
    name: '',
    location: '',
    blocks_count: 1,
    shelves_per_block: 1,
    cells_per_shelf: 10
  });

  const [alerts, setAlerts] = useState([]);

  const showAlert = (message, type = 'info') => {
    const id = Date.now();
    setAlerts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setAlerts(prev => prev.filter(alert => alert.id !== id));
    }, 5000);
  };

  const apiCall = async (endpoint, method = 'GET', data = null) => {
    try {
      const config = {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      if (data) {
        config.body = JSON.stringify(data);
      }

      const response = await fetch(`${BACKEND_URL}${endpoint}`, config);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Произошла ошибка');
      }

      return result;
    } catch (error) {
      showAlert(error.message, 'error');
      throw error;
    }
  };

  useEffect(() => {
    if (token) {
      // Попытка получить информацию о пользователе при загрузке
      fetchUserData();
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      fetchNotifications();
      if (user.role === 'admin') {
        fetchUsers();
        fetchAllCargo();
        fetchWarehouses();
      } else if (user.role === 'warehouse_operator') {
        fetchWarehouseCargo();
        fetchWarehouses();
      } else {
        fetchMyCargo();
      }
    }
  }, [user]);

  const fetchUserData = async () => {
    try {
      // Здесь можно добавить endpoint для получения данных пользователя
      // Пока оставим заглушку
    } catch (error) {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    }
  };

  const fetchNotifications = async () => {
    try {
      const data = await apiCall('/api/notifications');
      setNotifications(data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const fetchMyCargo = async () => {
    try {
      const data = await apiCall('/api/cargo/my');
      setCargo(data);
    } catch (error) {
      console.error('Error fetching cargo:', error);
    }
  };

  const fetchAllCargo = async () => {
    try {
      const data = await apiCall('/api/cargo/all');
      setCargo(data);
    } catch (error) {
      console.error('Error fetching all cargo:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const data = await apiCall('/api/admin/users');
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchWarehouseCargo = async () => {
    try {
      const data = await apiCall('/api/warehouse/cargo');
      setWarehouseCargo(data);
    } catch (error) {
      console.error('Error fetching warehouse cargo:', error);
    }
  };

  const fetchWarehouses = async () => {
    try {
      const data = await apiCall('/api/warehouses');
      setWarehouses(data);
    } catch (error) {
      console.error('Error fetching warehouses:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await apiCall('/api/auth/login', 'POST', loginForm);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      showAlert('Успешный вход в систему!', 'success');
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const data = await apiCall('/api/auth/register', 'POST', registerForm);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      showAlert('Регистрация прошла успешно!', 'success');
    } catch (error) {
      console.error('Register error:', error);
    }
  };

  const handleCreateCargo = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/cargo/create', 'POST', {
        ...cargoForm,
        weight: parseFloat(cargoForm.weight),
        declared_value: parseFloat(cargoForm.declared_value)
      });
      showAlert('Груз успешно создан!', 'success');
      setCargoForm({
        recipient_name: '',
        recipient_phone: '',
        route: 'moscow_to_tajikistan',
        weight: '',
        description: '',
        declared_value: '',
        sender_address: '',
        recipient_address: ''
      });
      fetchMyCargo();
    } catch (error) {
      console.error('Create cargo error:', error);
    }
  };

  const handleTrackCargo = async (e) => {
    e.preventDefault();
    try {
      const data = await apiCall(`/api/cargo/track/${trackingNumber}`);
      setTrackingResult(data);
      showAlert('Груз найден!', 'success');
    } catch (error) {
      setTrackingResult(null);
      console.error('Track cargo error:', error);
    }
  };

  const handleWarehouseSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      const data = await apiCall(`/api/warehouse/search?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults(data);
    } catch (error) {
      console.error('Search error:', error);
    }
  };

  const handleCreateWarehouse = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/warehouses/create', 'POST', {
        ...warehouseForm,
        blocks_count: parseInt(warehouseForm.blocks_count),
        shelves_per_block: parseInt(warehouseForm.shelves_per_block),
        cells_per_shelf: parseInt(warehouseForm.cells_per_shelf)
      });
      showAlert('Склад успешно создан!', 'success');
      setWarehouseForm({
        name: '',
        location: '',
        blocks_count: 1,
        shelves_per_block: 1,
        cells_per_shelf: 10
      });
      fetchWarehouses();
    } catch (error) {
      console.error('Create warehouse error:', error);
    }
  };

  const updateCargoStatus = async (cargoId, status, warehouseLocation = null) => {
    try {
      const params = new URLSearchParams({ status });
      if (warehouseLocation) {
        params.append('warehouse_location', warehouseLocation);
      }
      
      await apiCall(`/api/cargo/${cargoId}/status?${params}`, 'PUT');
      showAlert('Статус груза обновлен!', 'success');
      
      if (user.role === 'admin') {
        fetchAllCargo();
      } else if (user.role === 'warehouse_operator') {
        fetchWarehouseCargo();
      }
    } catch (error) {
      console.error('Update status error:', error);
    }
  };

  const toggleUserStatus = async (userId, isActive) => {
    try {
      await apiCall(`/api/admin/users/${userId}/status`, 'PUT', { is_active: !isActive });
      showAlert('Статус пользователя изменен!', 'success');
      fetchUsers();
    } catch (error) {
      console.error('Toggle user status error:', error);
    }
  };

  const deleteUser = async (userId) => {
    if (window.confirm('Вы уверены, что хотите удалить этого пользователя?')) {
      try {
        await apiCall(`/api/admin/users/${userId}`, 'DELETE');
        showAlert('Пользователь удален!', 'success');
        fetchUsers();
      } catch (error) {
        console.error('Delete user error:', error);
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setCargo([]);
    setUsers([]);
    setWarehouses([]);
    setNotifications([]);
    showAlert('Вы вышли из системы', 'info');
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      created: { label: 'Создан', variant: 'secondary' },
      accepted: { label: 'Принят', variant: 'default' },
      in_transit: { label: 'В пути', variant: 'default' },
      arrived_destination: { label: 'Прибыл', variant: 'default' },
      completed: { label: 'Доставлен', variant: 'default' }
    };
    
    const config = statusConfig[status] || { label: status, variant: 'secondary' };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return <Shield className="h-4 w-4" />;
      case 'warehouse_operator':
        return <Warehouse className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getRoleLabel = (role) => {
    const labels = {
      user: 'Пользователь',
      admin: 'Администратор',
      warehouse_operator: 'Оператор склада'
    };
    return labels[role] || role;
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-md mx-auto">
            <div className="text-center mb-8">
              <div className="flex items-center justify-center mb-4">
                <Truck className="h-12 w-12 text-blue-600 mr-2" />
                <h1 className="text-3xl font-bold text-gray-900">КаргоТранс</h1>
              </div>
              <p className="text-gray-600">Грузоперевозки Москва-Таджикистан</p>
            </div>

            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Вход</TabsTrigger>
                <TabsTrigger value="register">Регистрация</TabsTrigger>
              </TabsList>
              
              <TabsContent value="login">
                <Card>
                  <CardHeader>
                    <CardTitle>Вход в систему</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleLogin} className="space-y-4">
                      <div>
                        <Label htmlFor="login-phone">Телефон</Label>
                        <Input
                          id="login-phone"
                          type="tel"
                          placeholder="+7XXXXXXXXXX"
                          value={loginForm.phone}
                          onChange={(e) => setLoginForm({...loginForm, phone: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="login-password">Пароль</Label>
                        <Input
                          id="login-password"
                          type="password"
                          placeholder="Введите пароль"
                          value={loginForm.password}
                          onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                          required
                        />
                      </div>
                      <Button type="submit" className="w-full">Войти</Button>
                    </form>
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="register">
                <Card>
                  <CardHeader>
                    <CardTitle>Регистрация</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleRegister} className="space-y-4">
                      <div>
                        <Label htmlFor="register-name">ФИО</Label>
                        <Input
                          id="register-name"
                          placeholder="Введите полное имя"
                          value={registerForm.full_name}
                          onChange={(e) => setRegisterForm({...registerForm, full_name: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="register-phone">Телефон</Label>
                        <Input
                          id="register-phone"
                          type="tel"
                          placeholder="+7XXXXXXXXXX"
                          value={registerForm.phone}
                          onChange={(e) => setRegisterForm({...registerForm, phone: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="register-password">Пароль</Label>
                        <Input
                          id="register-password"
                          type="password"
                          placeholder="Минимум 6 символов"
                          value={registerForm.password}
                          onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="register-role">Роль</Label>
                        <Select value={registerForm.role} onValueChange={(value) => setRegisterForm({...registerForm, role: value})}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="user">Пользователь</SelectItem>
                            <SelectItem value="admin">Администратор</SelectItem>
                            <SelectItem value="warehouse_operator">Оператор склада</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button type="submit" className="w-full">Зарегистрироваться</Button>
                    </form>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Отслеживание без авторизации */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Search className="mr-2 h-5 w-5" />
                  Отследить груз
                </CardTitle>
                <CardDescription>Введите номер груза для отслеживания</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleTrackCargo} className="space-y-4">
                  <Input
                    placeholder="Номер груза"
                    value={trackingNumber}
                    onChange={(e) => setTrackingNumber(e.target.value)}
                    required
                  />
                  <Button type="submit" className="w-full">
                    <Search className="mr-2 h-4 w-4" />
                    Отследить
                  </Button>
                </form>
                
                {trackingResult && (
                  <div className="mt-4 p-4 border rounded-lg">
                    <h3 className="font-semibold mb-2">Информация о грузе:</h3>
                    <div className="space-y-2 text-sm">
                      <p><strong>Номер:</strong> {trackingResult.cargo_number}</p>
                      <p><strong>Получатель:</strong> {trackingResult.recipient_name}</p>
                      <p><strong>Статус:</strong> {getStatusBadge(trackingResult.status)}</p>
                      <p><strong>Вес:</strong> {trackingResult.weight} кг</p>
                      <p><strong>Маршрут:</strong> {trackingResult.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}</p>
                      {trackingResult.warehouse_location && (
                        <p><strong>Местоположение на складе:</strong> {trackingResult.warehouse_location}</p>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Alerts */}
        <div className="fixed top-4 right-4 space-y-2 z-50">
          {alerts.map((alert) => (
            <Alert key={alert.id} className={`max-w-sm ${alert.type === 'error' ? 'border-red-500' : alert.type === 'success' ? 'border-green-500' : 'border-blue-500'}`}>
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Truck className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">КаргоТранс</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {getRoleIcon(user.role)}
                <span className="text-sm font-medium">{user.full_name}</span>
                <Badge variant="outline">{getRoleLabel(user.role)}</Badge>
              </div>
              
              <div className="relative">
                <Bell className="h-5 w-5 text-gray-600" />
                {notifications.filter(n => !n.is_read).length > 0 && (
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {notifications.filter(n => !n.is_read).length}
                  </span>
                )}
              </div>
              
              <Button variant="outline" onClick={handleLogout}>
                Выйти
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 lg:grid-cols-6">
            <TabsTrigger value="cargo" className="flex items-center">
              <Package className="mr-2 h-4 w-4" />
              Грузы
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center">
              <Bell className="mr-2 h-4 w-4" />
              Уведомления
            </TabsTrigger>
            {user.role === 'admin' && (
              <>
                <TabsTrigger value="admin" className="flex items-center">
                  <Users className="mr-2 h-4 w-4" />
                  Пользователи
                </TabsTrigger>
                <TabsTrigger value="admin-cargo" className="flex items-center">
                  <Package className="mr-2 h-4 w-4" />
                  Все грузы
                </TabsTrigger>
              </>
            )}
            {user.role === 'warehouse_operator' && (
              <>
                <TabsTrigger value="warehouse" className="flex items-center">
                  <Warehouse className="mr-2 h-4 w-4" />
                  Склад
                </TabsTrigger>
                <TabsTrigger value="search" className="flex items-center">
                  <Search className="mr-2 h-4 w-4" />
                  Поиск
                </TabsTrigger>
              </>
            )}
          </TabsList>

          {/* Грузы пользователя */}
          <TabsContent value="cargo" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Создание нового груза */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Plus className="mr-2 h-5 w-5" />
                    Создать новый груз
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateCargo} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="recipient_name">Имя получателя</Label>
                        <Input
                          id="recipient_name"
                          value={cargoForm.recipient_name}
                          onChange={(e) => setCargoForm({...cargoForm, recipient_name: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="recipient_phone">Телефон получателя</Label>
                        <Input
                          id="recipient_phone"
                          type="tel"
                          value={cargoForm.recipient_phone}
                          onChange={(e) => setCargoForm({...cargoForm, recipient_phone: e.target.value})}
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="route">Маршрут</Label>
                      <Select value={cargoForm.route} onValueChange={(value) => setCargoForm({...cargoForm, route: value})}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="moscow_to_tajikistan">Москва → Таджикистан</SelectItem>
                          <SelectItem value="tajikistan_to_moscow">Таджикистан → Москва</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="weight">Вес (кг)</Label>
                        <Input
                          id="weight"
                          type="number"
                          step="0.1"
                          value={cargoForm.weight}
                          onChange={(e) => setCargoForm({...cargoForm, weight: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="declared_value">Объявленная стоимость</Label>
                        <Input
                          id="declared_value"
                          type="number"
                          step="0.01"
                          value={cargoForm.declared_value}
                          onChange={(e) => setCargoForm({...cargoForm, declared_value: e.target.value})}
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="description">Описание груза</Label>
                      <Textarea
                        id="description"
                        value={cargoForm.description}
                        onChange={(e) => setCargoForm({...cargoForm, description: e.target.value})}
                        required
                      />
                    </div>

                    <div>
                      <Label htmlFor="sender_address">Адрес отправителя</Label>
                      <Input
                        id="sender_address"
                        value={cargoForm.sender_address}
                        onChange={(e) => setCargoForm({...cargoForm, sender_address: e.target.value})}
                        required
                      />
                    </div>

                    <div>
                      <Label htmlFor="recipient_address">Адрес получателя</Label>
                      <Input
                        id="recipient_address"
                        value={cargoForm.recipient_address}
                        onChange={(e) => setCargoForm({...cargoForm, recipient_address: e.target.value})}
                        required
                      />
                    </div>

                    <Button type="submit" className="w-full">
                      <Plus className="mr-2 h-4 w-4" />
                      Создать груз
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Мои грузы */}
              <Card>
                <CardHeader>
                  <CardTitle>Мои грузы</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {cargo.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">У вас пока нет грузов</p>
                    ) : (
                      cargo.map((item) => (
                        <div key={item.id} className="border rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h3 className="font-semibold">{item.cargo_number}</h3>
                              <p className="text-sm text-gray-600">Получатель: {item.recipient_name}</p>
                            </div>
                            {getStatusBadge(item.status)}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                          <div className="flex justify-between items-center text-sm">
                            <span>{item.weight} кг</span>
                            <span>{item.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}</span>
                          </div>
                          {item.warehouse_location && (
                            <p className="text-sm text-blue-600 mt-2">
                              <MapPin className="inline h-4 w-4 mr-1" />
                              {item.warehouse_location}
                            </p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Уведомления */}
          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Bell className="mr-2 h-5 w-5" />
                  Уведомления
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {notifications.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">Уведомлений нет</p>
                  ) : (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`border rounded-lg p-4 ${!notification.is_read ? 'bg-blue-50 border-blue-200' : ''}`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-sm">{notification.message}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {new Date(notification.created_at).toLocaleString('ru-RU')}
                            </p>
                          </div>
                          {!notification.is_read && (
                            <Badge variant="secondary" className="ml-2">Новое</Badge>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Администрирование пользователей */}
          {user.role === 'admin' && (
            <TabsContent value="admin">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Users className="mr-2 h-5 w-5" />
                    Управление пользователями
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ФИО</TableHead>
                        <TableHead>Телефон</TableHead>
                        <TableHead>Роль</TableHead>
                        <TableHead>Статус</TableHead>
                        <TableHead>Действия</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((u) => (
                        <TableRow key={u.id}>
                          <TableCell className="font-medium">{u.full_name}</TableCell>
                          <TableCell>{u.phone}</TableCell>
                          <TableCell>
                            <div className="flex items-center">
                              {getRoleIcon(u.role)}
                              <span className="ml-2">{getRoleLabel(u.role)}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant={u.is_active ? 'default' : 'secondary'}>
                              {u.is_active ? 'Активен' : 'Заблокирован'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => toggleUserStatus(u.id, u.is_active)}
                              >
                                {u.is_active ? 'Заблокировать' : 'Разблокировать'}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteUser(u.id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Все грузы для администратора */}
          {user.role === 'admin' && (
            <TabsContent value="admin-cargo">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Package className="mr-2 h-5 w-5" />
                    Все грузы
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Номер</TableHead>
                        <TableHead>Отправитель</TableHead>
                        <TableHead>Получатель</TableHead>
                        <TableHead>Маршрут</TableHead>
                        <TableHead>Статус</TableHead>
                        <TableHead>Действия</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cargo.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell className="font-medium">{item.cargo_number}</TableCell>
                          <TableCell>{item.sender_id}</TableCell>
                          <TableCell>{item.recipient_name}</TableCell>
                          <TableCell>
                            {item.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}
                          </TableCell>
                          <TableCell>{getStatusBadge(item.status)}</TableCell>
                          <TableCell>
                            <div className="flex space-x-2">
                              <Select onValueChange={(value) => updateCargoStatus(item.id, value)}>
                                <SelectTrigger className="w-40">
                                  <SelectValue placeholder="Изменить статус" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="accepted">Принят</SelectItem>
                                  <SelectItem value="in_transit">В пути</SelectItem>
                                  <SelectItem value="arrived_destination">Прибыл</SelectItem>
                                  <SelectItem value="completed">Доставлен</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Склад */}
          {user.role === 'warehouse_operator' && (
            <TabsContent value="warehouse">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Warehouse className="mr-2 h-5 w-5" />
                    Управление складом
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {warehouseCargo.map((item) => (
                      <div key={item.id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <h3 className="font-semibold">{item.cargo_number}</h3>
                            <p className="text-sm text-gray-600">Получатель: {item.recipient_name}</p>
                            <p className="text-sm text-gray-600">Вес: {item.weight} кг</p>
                          </div>
                          {getStatusBadge(item.status)}
                        </div>
                        
                        <div className="flex space-x-2">
                          <Select onValueChange={(value) => updateCargoStatus(item.id, value)}>
                            <SelectTrigger className="w-40">
                              <SelectValue placeholder="Изменить статус" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="accepted">Принять</SelectItem>
                              <SelectItem value="in_transit">Отправить</SelectItem>
                              <SelectItem value="arrived_destination">Прибыл</SelectItem>
                              <SelectItem value="completed">Выдать</SelectItem>
                            </SelectContent>
                          </Select>
                          
                          <Input
                            placeholder="Местоположение на складе"
                            className="flex-1"
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                updateCargoStatus(item.id, item.status, e.target.value);
                                e.target.value = '';
                              }
                            }}
                          />
                        </div>
                        
                        {item.warehouse_location && (
                          <p className="text-sm text-blue-600 mt-2">
                            <MapPin className="inline h-4 w-4 mr-1" />
                            Текущее расположение: {item.warehouse_location}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Поиск для оператора склада */}
          {user.role === 'warehouse_operator' && (
            <TabsContent value="search">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Search className="mr-2 h-5 w-5" />
                    Поиск товара
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex space-x-2 mb-4">
                    <Input
                      placeholder="Поиск по номеру груза или имени получателя"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="flex-1"
                    />
                    <Button onClick={handleWarehouseSearch}>
                      <Search className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="space-y-4">
                    {searchResults.map((item) => (
                      <div key={item.id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-semibold">{item.cargo_number}</h3>
                            <p className="text-sm text-gray-600">Получатель: {item.recipient_name}</p>
                            <p className="text-sm text-gray-600">Описание: {item.description}</p>
                            <p className="text-sm text-gray-600">Вес: {item.weight} кг</p>
                            {item.warehouse_location && (
                              <p className="text-sm text-blue-600">
                                <MapPin className="inline h-4 w-4 mr-1" />
                                Расположение: {item.warehouse_location}
                              </p>
                            )}
                          </div>
                          {getStatusBadge(item.status)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </main>

      {/* Alerts */}
      <div className="fixed top-4 right-4 space-y-2 z-50">
        {alerts.map((alert) => (
          <Alert key={alert.id} className={`max-w-sm ${alert.type === 'error' ? 'border-red-500' : alert.type === 'success' ? 'border-green-500' : 'border-blue-500'}`}>
            <AlertDescription>{alert.message}</AlertDescription>
          </Alert>
        ))}
      </div>
    </div>
  );
}

export default App;