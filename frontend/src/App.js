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
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from './components/ui/dropdown-menu';
import { 
  Truck, Package, Users, Bell, Search, Plus, Edit, Trash2, CheckCircle, 
  Clock, MapPin, User, Shield, Warehouse, Menu, X, Building, 
  DollarSign, FileText, Grid3X3, Package2, Home, CreditCard, Printer, Zap, MessageCircle
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
  const [operatorCargoForm, setOperatorCargoForm] = useState({
    sender_full_name: '',
    sender_phone: '',
    recipient_full_name: '',
    recipient_phone: '',
    recipient_address: '',
    weight: '',
    declared_value: '',
    description: '',
    route: 'moscow_to_tajikistan'
  });
  const [operatorCargo, setOperatorCargo] = useState([]);
  const [availableCargo, setAvailableCargo] = useState([]);
  const [cargoHistory, setCargoHistory] = useState([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState('');
  const [availableCells, setAvailableCells] = useState([]);
  const [historyFilters, setHistoryFilters] = useState({
    status: 'all',
    search: ''
  });
  const [unpaidCargo, setUnpaidCargo] = useState([]);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [paymentModal, setPaymentModal] = useState(false);
  const [cargoForPayment, setCargoForPayment] = useState(null);
  const [paymentForm, setPaymentForm] = useState({
    cargo_number: '',
    amount_paid: '',
    transaction_type: 'cash',
    notes: ''
  });
  const [warehouseLayout, setWarehouseLayout] = useState(null);
  const [selectedWarehouseForLayout, setSelectedWarehouseForLayout] = useState(null);
  const [layoutModal, setLayoutModal] = useState(false);
  const [usersByRole, setUsersByRole] = useState({
    user: [],
    admin: [],
    warehouse_operator: []
  });
  const [cargoRequests, setCargoRequests] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [systemNotifications, setSystemNotifications] = useState([]);
  const [requestForm, setRequestForm] = useState({
    recipient_full_name: '',
    recipient_phone: '',
    recipient_address: '',
    pickup_address: '',
    cargo_name: '',
    weight: '',
    declared_value: '',
    description: '',
    route: 'moscow_to_tajikistan'
  });

  // Transport states
  const [transports, setTransports] = useState([]);
  const [transportForm, setTransportForm] = useState({
    driver_name: '',
    driver_phone: '',
    transport_number: '',
    capacity_kg: '',
    direction: ''
  });
  const [selectedTransport, setSelectedTransport] = useState(null);
  const [transportManagementModal, setTransportManagementModal] = useState(false);
  const [availableCargoForTransport, setAvailableCargoForTransport] = useState([]);
  const [selectedCargoForPlacement, setSelectedCargoForPlacement] = useState([]);
  const [transportCargoList, setTransportCargoList] = useState([]);
  const [contactModal, setContactModal] = useState(false);

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
        fetchOperatorCargo();
        fetchUsersByRole();
        fetchUnpaidCargo();
        fetchPaymentHistory();
        fetchCargoRequests();
        fetchSystemNotifications();
        fetchTransports();
      } else if (user.role === 'warehouse_operator') {
        fetchWarehouseCargo();
        fetchWarehouses();
        fetchOperatorCargo();
        fetchUnpaidCargo();
        fetchPaymentHistory();
        fetchCargoRequests();
        fetchSystemNotifications();
        fetchTransports();
      } else {
        fetchMyCargo();
        fetchMyRequests();
        fetchSystemNotifications();
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

  const fetchOperatorCargo = async () => {
    try {
      const data = await apiCall('/api/operator/cargo/list');
      setOperatorCargo(data);
    } catch (error) {
      console.error('Error fetching operator cargo:', error);
    }
  };

  const fetchAvailableCargo = async () => {
    try {
      const data = await apiCall('/api/operator/cargo/available');
      setAvailableCargo(data);
    } catch (error) {
      console.error('Error fetching available cargo:', error);
    }
  };

  const fetchCargoHistory = async () => {
    try {
      const params = new URLSearchParams();
      if (historyFilters.status && historyFilters.status !== 'all') {
        params.append('status', historyFilters.status);
      }
      if (historyFilters.search) {
        params.append('search', historyFilters.search);
      }
      const data = await apiCall(`/api/operator/cargo/history?${params}`);
      setCargoHistory(data);
    } catch (error) {
      console.error('Error fetching cargo history:', error);
    }
  };

  const fetchAvailableCells = async (warehouseId) => {
    try {
      const data = await apiCall(`/api/warehouses/${warehouseId}/available-cells`);
      setAvailableCells(data.available_cells || []);
    } catch (error) {
      console.error('Error fetching available cells:', error);
    }
  };

  const fetchUnpaidCargo = async () => {
    try {
      const data = await apiCall('/api/cashier/unpaid-cargo');
      setUnpaidCargo(data);
    } catch (error) {
      console.error('Error fetching unpaid cargo:', error);
    }
  };

  const fetchPaymentHistory = async () => {
    try {
      const data = await apiCall('/api/cashier/payment-history');
      setPaymentHistory(data);
    } catch (error) {
      console.error('Error fetching payment history:', error);
    }
  };

  const fetchUsersByRole = async () => {
    try {
      const roles = ['user', 'admin', 'warehouse_operator'];
      const usersByRoleData = {};
      
      for (const role of roles) {
        const data = await apiCall(`/api/admin/users/by-role/${role}`);
        usersByRoleData[role] = data;
      }
      
      setUsersByRole(usersByRoleData);
    } catch (error) {
      console.error('Error fetching users by role:', error);
    }
  };

  const fetchWarehouseLayout = async (warehouseId) => {
    try {
      const data = await apiCall(`/api/warehouses/${warehouseId}/full-layout`);
      setWarehouseLayout(data);
    } catch (error) {
      console.error('Error fetching warehouse layout:', error);
    }
  };

  const fetchCargoRequests = async () => {
    try {
      const data = await apiCall('/api/admin/cargo-requests');
      setCargoRequests(data);
    } catch (error) {
      console.error('Error fetching cargo requests:', error);
    }
  };

  const fetchMyRequests = async () => {
    try {
      const data = await apiCall('/api/user/my-requests');
      setMyRequests(data);
    } catch (error) {
      console.error('Error fetching my requests:', error);
    }
  };

  const fetchSystemNotifications = async () => {
    try {
      const data = await apiCall('/api/system-notifications');
      setSystemNotifications(data);
    } catch (error) {
      console.error('Error fetching system notifications:', error);
    }
  };

  // Transport functions
  const fetchTransports = async (status = null) => {
    try {
      const params = status ? `?status=${status}` : '';
      const data = await apiCall(`/api/transport/list${params}`);
      setTransports(data);
    } catch (error) {
      console.error('Error fetching transports:', error);
    }
  };

  const fetchTransportCargoList = async (transportId) => {
    try {
      const data = await apiCall(`/api/transport/${transportId}/cargo-list`);
      setTransportCargoList(data);
    } catch (error) {
      console.error('Error fetching transport cargo list:', error);
    }
  };

  const fetchAvailableCargoForTransport = async () => {
    try {
      // Получить грузы, которые находятся на складе и готовы для загрузки
      const data = await apiCall('/api/operator/cargo/available');
      setAvailableCargoForTransport(data.filter(cargo => 
        cargo.status === 'accepted' && cargo.warehouse_location
      ));
    } catch (error) {
      console.error('Error fetching available cargo for transport:', error);
    }
  };

  const handleCreateTransport = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/transport/create', 'POST', {
        ...transportForm,
        capacity_kg: parseFloat(transportForm.capacity_kg)
      });
      showAlert('Транспорт успешно добавлен!', 'success');
      setTransportForm({
        driver_name: '',
        driver_phone: '',
        transport_number: '',
        capacity_kg: '',
        direction: ''
      });
      fetchTransports();
    } catch (error) {
      console.error('Create transport error:', error);
    }
  };

  const handlePlaceCargoOnTransport = async (transportId, cargoIds) => {
    try {
      await apiCall(`/api/transport/${transportId}/place-cargo`, 'POST', {
        transport_id: transportId,
        cargo_ids: cargoIds
      });
      showAlert('Груз успешно размещен на транспорте!', 'success');
      fetchTransports();
      fetchTransportCargoList(transportId);
      setSelectedCargoForPlacement([]);
    } catch (error) {
      console.error('Place cargo on transport error:', error);
    }
  };

  const handleDispatchTransport = async (transportId) => {
    if (window.confirm('Вы уверены, что хотите отправить этот транспорт?')) {
      try {
        await apiCall(`/api/transport/${transportId}/dispatch`, 'POST');
        showAlert('Транспорт отправлен!', 'success');
        fetchTransports();
        setTransportManagementModal(false);
      } catch (error) {
        console.error('Dispatch transport error:', error);
      }
    }
  };

  const handleDeleteTransport = async (transportId) => {
    if (window.confirm('Вы уверены, что хотите удалить этот транспорт?')) {
      try {
        await apiCall(`/api/transport/${transportId}`, 'DELETE');
        showAlert('Транспорт удален!', 'success');
        fetchTransports();
        setTransportManagementModal(false);
      } catch (error) {
        console.error('Delete transport error:', error);
      }
    }
  };

  // Contact functions
  const handleWhatsAppContact = () => {
    // Открыть WhatsApp с предустановленным сообщением
    const phoneNumber = "79123456789"; // Номер службы поддержки
    const message = "Здравствуйте! У меня есть вопрос по грузоперевозкам TAJLINE.TJ";
    const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  const handleTelegramContact = () => {
    // Открыть Telegram
    const telegramUsername = "tajline_support"; // Username службы поддержки
    const telegramUrl = `https://t.me/${telegramUsername}`;
    window.open(telegramUrl, '_blank');
  };

  const handleOnlineChat = () => {
    // Здесь можно интегрировать онлайн чат (например, Tawk.to, Intercom, или собственное решение)
    showAlert('Онлайн чат временно недоступен. Пожалуйста, используйте WhatsApp или Telegram.', 'info');
    // Альтернативно можно открыть форму обратной связи
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

  const handleAcceptCargo = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/operator/cargo/accept', 'POST', {
        ...operatorCargoForm,
        weight: parseFloat(operatorCargoForm.weight),
        declared_value: parseFloat(operatorCargoForm.declared_value)
      });
      showAlert('Груз успешно принят!', 'success');
      setOperatorCargoForm({
        sender_full_name: '',
        sender_phone: '',
        recipient_full_name: '',
        recipient_phone: '',
        recipient_address: '',
        weight: '',
        declared_value: '',
        description: '',
        route: 'moscow_to_tajikistan'
      });
      fetchOperatorCargo();
      fetchAvailableCargo();
    } catch (error) {
      console.error('Accept cargo error:', error);
    }
  };

  const handlePlaceCargo = async (cargoId, warehouseId, blockNumber, shelfNumber, cellNumber) => {
    try {
      await apiCall('/api/operator/cargo/place', 'POST', {
        cargo_id: cargoId,
        warehouse_id: warehouseId,
        block_number: parseInt(blockNumber),
        shelf_number: parseInt(shelfNumber),
        cell_number: parseInt(cellNumber)
      });
      showAlert('Груз успешно размещен на складе!', 'success');
      fetchOperatorCargo();
      fetchAvailableCargo();
      fetchAvailableCells(warehouseId);
    } catch (error) {
      console.error('Place cargo error:', error);
    }
  };

  const handleSearchCargoForPayment = async () => {
    if (!paymentForm.cargo_number.trim()) return;
    
    try {
      const data = await apiCall(`/api/cashier/search-cargo/${paymentForm.cargo_number}`);
      setCargoForPayment(data);
      setPaymentForm({...paymentForm, amount_paid: data.declared_value.toString()});
    } catch (error) {
      setCargoForPayment(null);
      console.error('Search cargo for payment error:', error);
    }
  };

  const handleProcessPayment = async () => {
    try {
      await apiCall('/api/cashier/process-payment', 'POST', {
        cargo_number: paymentForm.cargo_number,
        amount_paid: parseFloat(paymentForm.amount_paid),
        transaction_type: paymentForm.transaction_type,
        notes: paymentForm.notes
      });
      showAlert('Оплата успешно принята!', 'success');
      setPaymentModal(false);
      setCargoForPayment(null);
      setPaymentForm({
        cargo_number: '',
        amount_paid: '',
        transaction_type: 'cash',
        notes: ''
      });
      fetchUnpaidCargo();
      fetchPaymentHistory();
      fetchOperatorCargo();
    } catch (error) {
      console.error('Process payment error:', error);
    }
  };

  const handleOpenWarehouseLayout = async (warehouse) => {
    setSelectedWarehouseForLayout(warehouse);
    await fetchWarehouseLayout(warehouse.id);
    setLayoutModal(true);
  };

  const printCargoInvoice = (cargo) => {
    const printWindow = window.open('', '_blank');
    const invoiceHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>Накладная - ${cargo.cargo_number}</title>
        <style>
          @page { size: A5; margin: 10mm; }
          body { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; margin: 0; }
          .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
          .logo { font-size: 24px; font-weight: bold; color: #0066cc; margin-bottom: 5px; }
          .company { font-size: 14px; color: #666; }
          .title { text-align: center; font-size: 16px; font-weight: bold; margin: 15px 0; }
          .section { margin-bottom: 15px; }
          .section-title { font-weight: bold; background: #f0f0f0; padding: 5px; margin-bottom: 8px; }
          .info-row { display: flex; justify-content: space-between; margin-bottom: 5px; }
          .info-label { font-weight: bold; }
          .footer { margin-top: 20px; text-align: center; font-size: 10px; color: #666; }
          .signature { margin-top: 30px; display: flex; justify-content: space-between; }
          .signature div { width: 45%; text-align: center; border-top: 1px solid #333; padding-top: 5px; }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo">TAJLINE.TJ</div>
          <div class="company">Грузоперевозки Москва-Таджикистан</div>
        </div>
        
        <div class="title">НАКЛАДНАЯ № ${cargo.cargo_number}</div>
        
        <div class="section">
          <div class="section-title">Информация о грузе</div>
          <div class="info-row">
            <span class="info-label">Дата приема:</span>
            <span>${new Date(cargo.created_at).toLocaleDateString('ru-RU')} ${new Date(cargo.created_at).toLocaleTimeString('ru-RU')}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Маршрут:</span>
            <span>${cargo.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Описание:</span>
            <span>${cargo.description}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Вес:</span>
            <span>${cargo.weight} кг</span>
          </div>
          <div class="info-row">
            <span class="info-label">Объявленная стоимость:</span>
            <span>${cargo.declared_value} ₽</span>
          </div>
        </div>
        
        <div class="section">
          <div class="section-title">Отправитель</div>
          <div class="info-row">
            <span class="info-label">ФИО:</span>
            <span>${cargo.sender_full_name || cargo.sender_id}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Телефон:</span>
            <span>${cargo.sender_phone || 'Не указан'}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Адрес:</span>
            <span>${cargo.sender_address || 'Не указан'}</span>
          </div>
        </div>
        
        <div class="section">
          <div class="section-title">Получатель</div>
          <div class="info-row">
            <span class="info-label">ФИО:</span>
            <span>${cargo.recipient_full_name || cargo.recipient_name}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Телефон:</span>
            <span>${cargo.recipient_phone}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Адрес:</span>
            <span>${cargo.recipient_address}</span>
          </div>
        </div>
        
        ${cargo.warehouse_location ? `
        <div class="section">
          <div class="section-title">Размещение</div>
          <div class="info-row">
            <span class="info-label">Местоположение:</span>
            <span>${cargo.warehouse_location}</span>
          </div>
        </div>
        ` : ''}
        
        <div class="signature">
          <div>
            Сдал: ________________<br>
            <small>подпись отправителя</small>
          </div>
          <div>
            Принял: ________________<br>
            <small>подпись сотрудника</small>
          </div>
        </div>
        
        <div class="footer">
          TAJLINE.TJ - Ваш надежный партнер в грузоперевозках<br>
          Дата печати: ${new Date().toLocaleDateString('ru-RU')} ${new Date().toLocaleTimeString('ru-RU')}
        </div>
      </body>
      </html>
    `;
    
    printWindow.document.write(invoiceHtml);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 500);
  };

  const handleCreateRequest = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/user/cargo-request', 'POST', {
        ...requestForm,
        weight: parseFloat(requestForm.weight),
        declared_value: parseFloat(requestForm.declared_value)
      });
      showAlert('Заявка на груз успешно подана!', 'success');
      setRequestForm({
        recipient_full_name: '',
        recipient_phone: '',
        recipient_address: '',
        pickup_address: '',
        cargo_name: '',
        weight: '',
        declared_value: '',
        description: '',
        route: 'moscow_to_tajikistan'
      });
      fetchMyRequests();
    } catch (error) {
      console.error('Create request error:', error);
    }
  };

  const handleAcceptRequest = async (requestId) => {
    try {
      await apiCall(`/api/admin/cargo-requests/${requestId}/accept`, 'POST');
      showAlert('Заявка принята и груз создан!', 'success');
      fetchCargoRequests();
      fetchOperatorCargo();
      fetchSystemNotifications();
    } catch (error) {
      console.error('Accept request error:', error);
    }
  };

  const handleRejectRequest = async (requestId, reason = '') => {
    try {
      await apiCall(`/api/admin/cargo-requests/${requestId}/reject`, 'POST', { reason });
      showAlert('Заявка отклонена', 'info');
      fetchCargoRequests();
      fetchSystemNotifications();
    } catch (error) {
      console.error('Reject request error:', error);
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
    setOperatorCargo([]);
    setAvailableCargo([]);
    setCargoHistory([]);
    setUnpaidCargo([]);
    setPaymentHistory([]);
    setNotifications([]);
    setUsersByRole({ user: [], admin: [], warehouse_operator: [] });
    // Clear transport states
    setTransports([]);
    setSelectedTransport(null);
    setTransportCargoList([]);
    setAvailableCargoForTransport([]);
    setSelectedCargoForPlacement([]);
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

  // Боковое меню для админа и оператора склада
  const SidebarMenu = () => {
    if (user?.role === 'user') return null;

    const menuItems = [
      {
        id: 'dashboard',
        label: 'Главная',
        icon: <Home className="w-5 h-5" />,
        section: 'dashboard'
      },
      {
        id: 'users',
        label: 'Пользователи',
        icon: <Users className="w-5 h-5" />,
        section: 'users',
        adminOnly: true,
        subsections: [
          { id: 'users-regular', label: 'Пользователи' },
          { id: 'users-operators', label: 'Операторы склада' },
          { id: 'users-admins', label: 'Администраторы' }
        ]
      },
      {
        id: 'cargo-management',
        label: 'Грузы',
        icon: <Package className="w-5 h-5" />,
        section: 'cargo-management',
        subsections: [
          { id: 'cargo-accept', label: 'Принимать новый груз' },
          { id: 'cargo-list', label: 'Список грузов' },
          { id: 'cargo-placement', label: 'Размещение груза' },
          { id: 'cargo-history', label: 'История грузов' }
        ]
      },
      {
        id: 'warehouses',
        label: 'Склады',
        icon: <Building className="w-5 h-5" />,
        section: 'warehouses',
        subsections: [
          { id: 'warehouses-list', label: 'Список складов' },
          { id: 'warehouses-create', label: 'Создать склад' },
          { id: 'warehouses-manage', label: 'Управление товарами' }
        ]
      },
      {
        id: 'notifications-management',
        label: 'Уведомления',
        icon: <Bell className="w-5 h-5" />,
        section: 'notifications-management',
        subsections: [
          { id: 'notifications-requests', label: 'Новые заявки' },
          { id: 'notifications-system', label: 'Уведомления' }
        ]
      },
      {
        id: 'cashier',
        label: 'Касса',
        icon: <DollarSign className="w-5 h-5" />,
        section: 'cashier',
        subsections: [
          { id: 'cashier-payment', label: 'Приём оплаты' },
          { id: 'cashier-unpaid', label: 'Не оплачено' },
          { id: 'cashier-history', label: 'История оплаты' }
        ]
      },
      {
        id: 'logistics',
        label: 'Логистика',
        icon: <Zap className="w-5 h-5" />,
        section: 'logistics',
        subsections: [
          { id: 'logistics-add-transport', label: 'Приём машину' },
          { id: 'logistics-transport-list', label: 'Список транспортов' },
          { id: 'logistics-in-transit', label: 'В пути' },
          { id: 'logistics-arrived', label: 'На место назначение' },
          { id: 'logistics-history', label: 'История Транспортировки' }
        ]
      },
      {
        id: 'finances',
        label: 'Финансы',
        icon: <DollarSign className="w-5 h-5" />,
        section: 'finances',
        adminOnly: true,
        subsections: [
          { id: 'finances-overview', label: 'Обзор' },
          { id: 'finances-transactions', label: 'Транзакции' }
        ]
      },
      {
        id: 'reports',
        label: 'Отчеты',
        icon: <FileText className="w-5 h-5" />,
        section: 'reports',
        subsections: [
          { id: 'reports-cargo', label: 'Отчеты по грузам' },
          { id: 'reports-performance', label: 'Производительность' }
        ]
      }
    ];

    const filteredItems = menuItems.filter(item => 
      !item.adminOnly || user?.role === 'admin'
    );

    return (
      <div className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-40 ${
        sidebarOpen ? 'w-64' : 'w-16'
      }`}>
        <div className="p-4">
          <div className="flex items-center justify-between mb-8">
            {sidebarOpen && (
              <h2 className="text-xl font-bold">Панель управления</h2>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-white hover:bg-gray-800"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>

          <nav className="space-y-2">
            {filteredItems.map((item) => (
              <div key={item.id}>
                <button
                  onClick={() => setActiveSection(item.section)}
                  className={`w-full flex items-center px-3 py-2 rounded-lg transition-colors ${
                    activeSection === item.section
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  {item.icon}
                  {sidebarOpen && <span className="ml-3">{item.label}</span>}
                </button>
                
                {sidebarOpen && item.subsections && activeSection === item.section && (
                  <div className="ml-8 mt-2 space-y-1">
                    {item.subsections.map((sub) => (
                      <button
                        key={sub.id}
                        onClick={() => setActiveTab(sub.id)}
                        className="block w-full text-left px-3 py-1 text-sm text-gray-400 hover:text-white transition-colors"
                      >
                        {sub.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>
        </div>
      </div>
    );
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-md mx-auto">
            <div className="text-center mb-8">
              <div className="flex items-center justify-center mb-4">
                <div className="bg-blue-600 text-white p-2 rounded-lg mr-3">
                  <Truck className="h-12 w-12" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-blue-600">TAJLINE.TJ</h1>
                  <p className="text-gray-600">Грузоперевозки Москва-Таджикистан</p>
                </div>
              </div>
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
      {/* Боковое меню */}
      {user && (user.role === 'admin' || user.role === 'warehouse_operator') && <SidebarMenu />}
      
      {/* Основной контент */}
      <div className={`${
        user && (user.role === 'admin' || user.role === 'warehouse_operator') 
          ? (sidebarOpen ? 'ml-64' : 'ml-16') 
          : ''
      } transition-all duration-300`}>
        
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex items-center mr-6">
                  <div className="bg-blue-600 text-white p-2 rounded-lg mr-3">
                    <Truck className="h-8 w-8" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold text-blue-600">TAJLINE.TJ</h1>
                    <p className="text-sm text-gray-600">Грузоперевозки Москва-Таджикистан</p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  {getRoleIcon(user.role)}
                  <span className="text-sm font-medium">{user.full_name}</span>
                  <Badge variant="outline">{getRoleLabel(user.role)}</Badge>
                </div>
                
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <div className="relative cursor-pointer">
                      <Bell className="h-5 w-5 text-gray-600 hover:text-gray-800 transition-colors" />
                      {(notifications.filter(n => !n.is_read).length + systemNotifications.filter(n => !n.is_read).length) > 0 && (
                        <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                          {notifications.filter(n => !n.is_read).length + systemNotifications.filter(n => !n.is_read).length}
                        </span>
                      )}
                    </div>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-80 max-h-96 overflow-y-auto">
                    <div className="px-3 py-2 border-b">
                      <h3 className="font-semibold text-sm">Уведомления</h3>
                    </div>
                    
                    {/* Личные уведомления */}
                    {notifications.length > 0 && (
                      <>
                        <div className="px-3 py-1 bg-gray-50">
                          <p className="text-xs font-medium text-gray-600">Личные уведомления</p>
                        </div>
                        {notifications.slice(0, 5).map((notification) => (
                          <DropdownMenuItem key={`notification-${notification.id}`} className="flex-col items-start p-3 cursor-default">
                            <div className={`w-full ${!notification.is_read ? 'font-medium' : ''}`}>
                              <p className="text-sm leading-tight">{notification.message}</p>
                              <p className="text-xs text-gray-500 mt-1">
                                {new Date(notification.created_at).toLocaleString('ru-RU')}
                              </p>
                              {!notification.is_read && (
                                <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mt-1"></span>
                              )}
                            </div>
                          </DropdownMenuItem>
                        ))}
                        {notifications.length > 5 && (
                          <div className="px-3 py-1 text-xs text-gray-500 text-center">
                            И еще {notifications.length - 5} уведомлений...
                          </div>
                        )}
                      </>
                    )}
                    
                    {/* Системные уведомления */}
                    {systemNotifications.length > 0 && (
                      <>
                        {notifications.length > 0 && <DropdownMenuSeparator />}
                        <div className="px-3 py-1 bg-gray-50">
                          <p className="text-xs font-medium text-gray-600">Системные уведомления</p>
                        </div>
                        {systemNotifications.slice(0, 5).map((notification) => (
                          <DropdownMenuItem key={`system-${notification.id}`} className="flex-col items-start p-3 cursor-default">
                            <div className={`w-full ${!notification.is_read ? 'font-medium' : ''}`}>
                              <p className="text-sm leading-tight">{notification.message}</p>
                              <p className="text-xs text-gray-500 mt-1">
                                {new Date(notification.created_at).toLocaleString('ru-RU')}
                              </p>
                              {!notification.is_read && (
                                <span className="inline-block w-2 h-2 bg-red-500 rounded-full mt-1"></span>
                              )}
                            </div>
                          </DropdownMenuItem>
                        ))}
                        {systemNotifications.length > 5 && (
                          <div className="px-3 py-1 text-xs text-gray-500 text-center">
                            И еще {systemNotifications.length - 5} уведомлений...
                          </div>
                        )}
                      </>
                    )}
                    
                    {/* Если нет уведомлений */}
                    {notifications.length === 0 && systemNotifications.length === 0 && (
                      <div className="px-3 py-8 text-center text-gray-500 text-sm">
                        Нет уведомлений
                      </div>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
                
                <Button variant="outline" onClick={handleLogout}>
                  Выйти
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8">
          {/* Для обычных пользователей - старый интерфейс с табами */}
          {user?.role === 'user' ? (
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="requests" className="flex items-center">
                  <Plus className="mr-2 h-4 w-4" />
                  Заявки на груз
                </TabsTrigger>
                <TabsTrigger value="cargo" className="flex items-center">
                  <Package className="mr-2 h-4 w-4" />
                  Мои грузы
                </TabsTrigger>
                <TabsTrigger value="notifications" className="flex items-center">
                  <Bell className="mr-2 h-4 w-4" />
                  Уведомления
                </TabsTrigger>
              </TabsList>

              {/* Заявки на груз */}
              <TabsContent value="requests" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Создание заявки */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <Plus className="mr-2 h-5 w-5" />
                        Подать заявку на груз
                      </CardTitle>
                      <CardDescription>
                        Заполните форму для подачи заявки на отправку груза
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleCreateRequest} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="recipient_full_name">ФИО получателя</Label>
                            <Input
                              id="recipient_full_name"
                              value={requestForm.recipient_full_name}
                              onChange={(e) => setRequestForm({...requestForm, recipient_full_name: e.target.value})}
                              placeholder="Иванов Иван Иванович"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="recipient_phone">Телефон получателя</Label>
                            <Input
                              id="recipient_phone"
                              type="tel"
                              value={requestForm.recipient_phone}
                              onChange={(e) => setRequestForm({...requestForm, recipient_phone: e.target.value})}
                              placeholder="+992XXXXXXXXX"
                              required
                            />
                          </div>
                        </div>

                        <div>
                          <Label htmlFor="recipient_address">Адрес получения груза</Label>
                          <Input
                            id="recipient_address"
                            value={requestForm.recipient_address}
                            onChange={(e) => setRequestForm({...requestForm, recipient_address: e.target.value})}
                            placeholder="Душанбе, ул. Рудаки, 10, кв. 5"
                            required
                          />
                        </div>

                        <div>
                          <Label htmlFor="pickup_address">Адрес отправки груза</Label>
                          <Input
                            id="pickup_address"
                            value={requestForm.pickup_address}
                            onChange={(e) => setRequestForm({...requestForm, pickup_address: e.target.value})}
                            placeholder="Москва, ул. Тверская, 1"
                            required
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="cargo_name">Название груза</Label>
                            <Input
                              id="cargo_name"
                              value={requestForm.cargo_name}
                              onChange={(e) => setRequestForm({...requestForm, cargo_name: e.target.value})}
                              placeholder="Документы, личные вещи"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="route">Маршрут</Label>
                            <Select value={requestForm.route} onValueChange={(value) => setRequestForm({...requestForm, route: value})}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="moscow_to_tajikistan">Москва → Таджикистан</SelectItem>
                                <SelectItem value="tajikistan_to_moscow">Таджикистан → Москва</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="weight">Вес груза (кг)</Label>
                            <Input
                              id="weight"
                              type="number"
                              step="0.1"
                              value={requestForm.weight}
                              onChange={(e) => setRequestForm({...requestForm, weight: e.target.value})}
                              placeholder="10.5"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="declared_value">Объявленная стоимость (руб.)</Label>
                            <Input
                              id="declared_value"
                              type="number"
                              step="0.01"
                              value={requestForm.declared_value}
                              onChange={(e) => setRequestForm({...requestForm, declared_value: e.target.value})}
                              placeholder="5000"
                              required
                            />
                          </div>
                        </div>

                        <div>
                          <Label htmlFor="description">Описание груза</Label>
                          <Textarea
                            id="description"
                            value={requestForm.description}
                            onChange={(e) => setRequestForm({...requestForm, description: e.target.value})}
                            placeholder="Подробное описание содержимого груза..."
                            required
                          />
                        </div>

                        <Button type="submit" className="w-full">
                          <Plus className="mr-2 h-4 w-4" />
                          Подать заявку
                        </Button>
                      </form>
                    </CardContent>
                  </Card>

                  {/* Мои заявки */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Мои заявки ({myRequests.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {myRequests.length === 0 ? (
                          <p className="text-gray-500 text-center py-4">У вас пока нет заявок</p>
                        ) : (
                          myRequests.map((request) => (
                            <div key={request.id} className="border rounded-lg p-4">
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <h3 className="font-semibold">{request.request_number}</h3>
                                  <p className="text-sm text-gray-600">{request.cargo_name}</p>
                                </div>
                                <Badge variant={
                                  request.status === 'pending' ? 'secondary' :
                                  request.status === 'accepted' ? 'default' : 'destructive'
                                }>
                                  {request.status === 'pending' ? 'На рассмотрении' :
                                   request.status === 'accepted' ? 'Принята' : 'Отклонена'}
                                </Badge>
                              </div>
                              <div className="text-sm text-gray-600 space-y-1">
                                <p><strong>Получатель:</strong> {request.recipient_full_name}</p>
                                <p><strong>Вес:</strong> {request.weight} кг</p>
                                <p><strong>Маршрут:</strong> {request.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}</p>
                                <p><strong>Дата подачи:</strong> {new Date(request.created_at).toLocaleDateString('ru-RU')}</p>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
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
            </Tabs>
          ) : (
            /* Для админа и оператора склада - новый интерфейс с боковым меню */
            <div className="space-y-6">
              {/* Dashboard */}
              {activeSection === 'dashboard' && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Всего грузов</CardTitle>
                      <Package className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{cargo.length}</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Активные пользователи</CardTitle>
                      <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{users.filter(u => u.is_active).length}</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Склады</CardTitle>
                      <Building className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{warehouses.length}</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Непрочитанные уведомления</CardTitle>
                      <Bell className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{notifications.filter(n => !n.is_read).length}</div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Управление грузами */}
              {activeSection === 'cargo-management' && (
                <div className="space-y-6">
                  {/* Принимать новый груз */}
                  {activeTab === 'cargo-accept' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Plus className="mr-2 h-5 w-5" />
                          Принимать новый груз
                        </CardTitle>
                        <CardDescription>
                          Заполните форму для приема нового груза от клиента
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleAcceptCargo} className="space-y-4 max-w-2xl">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <Label htmlFor="sender_full_name">ФИО отправителя</Label>
                              <Input
                                id="sender_full_name"
                                value={operatorCargoForm.sender_full_name}
                                onChange={(e) => setOperatorCargoForm({...operatorCargoForm, sender_full_name: e.target.value})}
                                placeholder="Иванов Иван Иванович"
                                required
                              />
                            </div>
                            <div>
                              <Label htmlFor="sender_phone">Телефон отправителя</Label>
                              <Input
                                id="sender_phone"
                                type="tel"
                                value={operatorCargoForm.sender_phone}
                                onChange={(e) => setOperatorCargoForm({...operatorCargoForm, sender_phone: e.target.value})}
                                placeholder="+7XXXXXXXXXX"
                                required
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <Label htmlFor="recipient_full_name">ФИО получателя</Label>
                              <Input
                                id="recipient_full_name"
                                value={operatorCargoForm.recipient_full_name}
                                onChange={(e) => setOperatorCargoForm({...operatorCargoForm, recipient_full_name: e.target.value})}
                                placeholder="Петров Петр Петрович"
                                required
                              />
                            </div>
                            <div>
                              <Label htmlFor="recipient_phone">Телефон получателя</Label>
                              <Input
                                id="recipient_phone"
                                type="tel"
                                value={operatorCargoForm.recipient_phone}
                                onChange={(e) => setOperatorCargoForm({...operatorCargoForm, recipient_phone: e.target.value})}
                                placeholder="+992XXXXXXXXX"
                                required
                              />
                            </div>
                          </div>

                          <div>
                            <Label htmlFor="recipient_address">Адрес получения груза</Label>
                            <Input
                              id="recipient_address"
                              value={operatorCargoForm.recipient_address}
                              onChange={(e) => setOperatorCargoForm({...operatorCargoForm, recipient_address: e.target.value})}
                              placeholder="Душанбе, ул. Рудаки, 10, кв. 5"
                              required
                            />
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <Label htmlFor="weight">Вес груза (кг)</Label>
                              <Input
                                id="weight"
                                type="number"
                                step="0.1"
                                value={operatorCargoForm.weight}
                                onChange={(e) => setOperatorCargoForm({...operatorCargoForm, weight: e.target.value})}
                                placeholder="10.5"
                                required
                              />
                            </div>
                            <div>
                              <Label htmlFor="declared_value">Стоимость груза (руб.)</Label>
                              <Input
                                id="declared_value"
                                type="number"
                                step="0.01"
                                value={operatorCargoForm.declared_value}
                                onChange={(e) => setOperatorCargoForm({...operatorCargoForm, declared_value: e.target.value})}
                                placeholder="5000"
                                required
                              />
                            </div>
                            <div>
                              <Label htmlFor="route">Маршрут</Label>
                              <Select value={operatorCargoForm.route} onValueChange={(value) => setOperatorCargoForm({...operatorCargoForm, route: value})}>
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="moscow_to_tajikistan">Москва → Таджикистан</SelectItem>
                                  <SelectItem value="tajikistan_to_moscow">Таджикистан → Москва</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>

                          <div>
                            <Label htmlFor="description">Описание груза</Label>
                            <Textarea
                              id="description"
                              value={operatorCargoForm.description}
                              onChange={(e) => setOperatorCargoForm({...operatorCargoForm, description: e.target.value})}
                              placeholder="Личные вещи, документы, подарки..."
                              required
                            />
                          </div>

                          <Button type="submit" className="w-full">
                            <Plus className="mr-2 h-4 w-4" />
                            Принять груз
                          </Button>
                        </form>
                      </CardContent>
                    </Card>
                  )}

                  {/* Список грузов */}
                  {(activeTab === 'cargo-list' || !activeTab || activeTab === 'cargo-management') && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Package className="mr-2 h-5 w-5" />
                            Список грузов
                          </div>
                          <Button onClick={() => {setActiveTab('cargo-accept'); fetchOperatorCargo();}}>
                            <Plus className="mr-2 h-4 w-4" />
                            Принять груз
                          </Button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {operatorCargo.length === 0 ? (
                            <div className="text-center py-8">
                              <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500 mb-4">Нет принятых грузов</p>
                              <Button onClick={() => setActiveTab('cargo-accept')}>
                                <Plus className="mr-2 h-4 w-4" />
                                Принять первый груз
                              </Button>
                            </div>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Номер груза</TableHead>
                                  <TableHead>Отправитель</TableHead>
                                  <TableHead>Получатель</TableHead>
                                  <TableHead>Вес</TableHead>
                                  <TableHead>Стоимость</TableHead>
                                  <TableHead>Статус оплаты</TableHead>
                                  <TableHead>Расположение</TableHead>
                                  <TableHead>Дата приема</TableHead>
                              <TableHead>Действия</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {operatorCargo.map((item) => (
                                  <TableRow key={item.id}>
                                    <TableCell className="font-medium">{item.cargo_number}</TableCell>
                                    <TableCell>
                                      <div>
                                        <div className="font-medium">{item.sender_full_name}</div>
                                        <div className="text-sm text-gray-500">{item.sender_phone}</div>
                                      </div>
                                    </TableCell>
                                    <TableCell>
                                      <div>
                                        <div className="font-medium">{item.recipient_full_name}</div>
                                        <div className="text-sm text-gray-500">{item.recipient_phone}</div>
                                        <div className="text-sm text-gray-500">{item.recipient_address}</div>
                                      </div>
                                    </TableCell>
                                    <TableCell>{item.weight} кг</TableCell>
                                    <TableCell>{item.declared_value} ₽</TableCell>
                                    <TableCell>
                                      <Badge variant={item.payment_status === 'paid' ? 'default' : 'secondary'}>
                                        {item.payment_status === 'paid' ? 'Оплачен' : 'Ожидает оплаты'}
                                      </Badge>
                                    </TableCell>
                                    <TableCell>
                                      {item.warehouse_location ? (
                                        <div className="text-sm">
                                          <div className="font-medium">{warehouses.find(w => w.id === item.warehouse_id)?.name || 'Склад'}</div>
                                          <div className="text-blue-600">{item.warehouse_location}</div>
                                        </div>
                                      ) : (
                                        <Badge variant="outline">Не размещен</Badge>
                                      )}
                                    </TableCell>
                                    <TableCell>
                                      {new Date(item.created_at).toLocaleDateString('ru-RU')} {new Date(item.created_at).toLocaleTimeString('ru-RU')}
                                    </TableCell>
                                    <TableCell>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => printCargoInvoice(item)}
                                        className="flex items-center"
                                      >
                                        <Printer className="mr-1 h-4 w-4" />
                                        Печать накладной
                                      </Button>
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Размещение груза */}
                  {activeTab === 'cargo-placement' && (
                    <div className="space-y-6">
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center">
                            <Grid3X3 className="mr-2 h-5 w-5" />
                            Размещение груза на складе
                          </CardTitle>
                          <CardDescription>
                            Выберите груз и разместите его в свободной ячейке склада
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Button onClick={fetchAvailableCargo} className="mb-4">
                            Обновить список грузов
                          </Button>
                          
                          <div className="space-y-4">
                            {availableCargo.length === 0 ? (
                              <div className="text-center py-8">
                                <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                                <p className="text-gray-500">Нет грузов для размещения</p>
                              </div>
                            ) : (
                              availableCargo.map((item) => (
                                <div key={item.id} className="border rounded-lg p-4">
                                  <div className="flex justify-between items-start mb-4">
                                    <div>
                                      <h3 className="font-semibold text-lg">{item.cargo_number}</h3>
                                      <div className="text-sm text-gray-600 space-y-1">
                                        <p><strong>От:</strong> {item.sender_full_name} ({item.sender_phone})</p>
                                        <p><strong>Для:</strong> {item.recipient_full_name} ({item.recipient_phone})</p>
                                        <p><strong>Вес:</strong> {item.weight} кг</p>
                                        <p><strong>Описание:</strong> {item.description}</p>
                                      </div>
                                    </div>
                                    {getStatusBadge(item.status)}
                                  </div>
                                  
                                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                                    <div>
                                      <Label>Склад</Label>
                                      <Select 
                                        value={selectedWarehouse} 
                                        onValueChange={(warehouseId) => {
                                          setSelectedWarehouse(warehouseId);
                                          fetchAvailableCells(warehouseId);
                                        }}
                                      >
                                        <SelectTrigger>
                                          <SelectValue placeholder="Выберите склад" />
                                        </SelectTrigger>
                                        <SelectContent>
                                          {warehouses.map((warehouse) => (
                                            <SelectItem key={warehouse.id} value={warehouse.id}>
                                              {warehouse.name}
                                            </SelectItem>
                                          ))}
                                        </SelectContent>
                                      </Select>
                                    </div>
                                    
                                    {selectedWarehouse && availableCells.length > 0 && (
                                      <>
                                        <div>
                                          <Label>Свободные места</Label>
                                          <Select onValueChange={(locationCode) => {
                                            const [block, shelf, cell] = locationCode.split('-').map(part => parseInt(part.substring(1)));
                                            handlePlaceCargo(item.id, selectedWarehouse, block, shelf, cell);
                                          }}>
                                            <SelectTrigger>
                                              <SelectValue placeholder="Выберите место" />
                                            </SelectTrigger>
                                            <SelectContent>
                                              {availableCells.slice(0, 20).map((cell) => (
                                                <SelectItem key={cell.id} value={cell.location_code}>
                                                  {cell.location_code}
                                                </SelectItem>
                                              ))}
                                            </SelectContent>
                                          </Select>
                                        </div>
                                        <div className="text-sm text-green-600">
                                          Доступно: {availableCells.length} ячеек
                                        </div>
                                      </>
                                    )}
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}

                  {/* История грузов */}
                  {activeTab === 'cargo-history' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <FileText className="mr-2 h-5 w-5" />
                          История грузов
                        </CardTitle>
                        <CardDescription>
                          Просмотр доставленных грузов с фильтрами и поиском
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex space-x-4 mb-6">
                          <div className="flex-1">
                            <Input
                              placeholder="Поиск по номеру груза, отправителю или получателю"
                              value={historyFilters.search}
                              onChange={(e) => setHistoryFilters({...historyFilters, search: e.target.value})}
                            />
                          </div>
                          <div>
                            <Select 
                              value={historyFilters.status} 
                              onValueChange={(value) => setHistoryFilters({...historyFilters, status: value})}
                            >
                              <SelectTrigger className="w-48">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="all">Все статусы оплаты</SelectItem>
                                <SelectItem value="paid">Оплачено</SelectItem>
                                <SelectItem value="pending">Ожидает оплаты</SelectItem>
                                <SelectItem value="failed">Оплата не прошла</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <Button onClick={fetchCargoHistory}>
                            <Search className="mr-2 h-4 w-4" />
                            Найти
                          </Button>
                        </div>
                        
                        <div className="space-y-4">
                          {cargoHistory.length === 0 ? (
                            <div className="text-center py-8">
                              <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">История грузов пуста</p>
                            </div>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Номер</TableHead>
                                  <TableHead>Отправитель</TableHead>
                                  <TableHead>Получатель</TableHead>
                                  <TableHead>Вес</TableHead>
                                  <TableHead>Стоимость</TableHead>
                                  <TableHead>Статус оплаты</TableHead>
                                  <TableHead>Дата доставки</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {cargoHistory.map((item) => (
                                  <TableRow key={item.id}>
                                    <TableCell className="font-medium">{item.cargo_number}</TableCell>
                                    <TableCell>
                                      <div>
                                        <div className="font-medium">{item.sender_full_name}</div>
                                        <div className="text-sm text-gray-500">{item.sender_phone}</div>
                                      </div>
                                    </TableCell>
                                    <TableCell>
                                      <div>
                                        <div className="font-medium">{item.recipient_full_name}</div>
                                        <div className="text-sm text-gray-500">{item.recipient_phone}</div>
                                      </div>
                                    </TableCell>
                                    <TableCell>{item.weight} кг</TableCell>
                                    <TableCell>{item.declared_value} ₽</TableCell>
                                    <TableCell>
                                      <Badge variant={item.payment_status === 'paid' ? 'default' : 'secondary'}>
                                        {item.payment_status === 'paid' ? 'Оплачен' : 'Не оплачен'}
                                      </Badge>
                                    </TableCell>
                                    <TableCell>
                                      {new Date(item.updated_at).toLocaleDateString('ru-RU')}
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
              {/* Управление пользователями (только для админа) */}
              {activeSection === 'users' && user?.role === 'admin' && (
                <div className="space-y-6">
                  {/* Пользователи */}
                  {(activeTab === 'users-regular' || !activeTab || activeTab === 'users') && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <User className="mr-2 h-5 w-5" />
                          Пользователи ({usersByRole.user.length})
                        </CardTitle>
                        <CardDescription>Обычные пользователи системы</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>ФИО</TableHead>
                              <TableHead>Телефон</TableHead>
                              <TableHead>Дата регистрации</TableHead>
                              <TableHead>Статус</TableHead>
                              <TableHead>Действия</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {usersByRole.user.map((u) => (
                              <TableRow key={u.id}>
                                <TableCell className="font-medium">{u.full_name}</TableCell>
                                <TableCell>{u.phone}</TableCell>
                                <TableCell>{new Date(u.created_at).toLocaleDateString('ru-RU')}</TableCell>
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
                  )}

                  {/* Операторы склада */}
                  {activeTab === 'users-operators' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Warehouse className="mr-2 h-5 w-5" />
                          Операторы складов ({usersByRole.warehouse_operator.length})
                        </CardTitle>
                        <CardDescription>Операторы складов и кассиры</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>ФИО</TableHead>
                              <TableHead>Телефон</TableHead>
                              <TableHead>Дата регистрации</TableHead>
                              <TableHead>Статус</TableHead>
                              <TableHead>Действия</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {usersByRole.warehouse_operator.map((u) => (
                              <TableRow key={u.id}>
                                <TableCell className="font-medium">{u.full_name}</TableCell>
                                <TableCell>{u.phone}</TableCell>
                                <TableCell>{new Date(u.created_at).toLocaleDateString('ru-RU')}</TableCell>
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
                  )}

                  {/* Администраторы */}
                  {activeTab === 'users-admins' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Shield className="mr-2 h-5 w-5" />
                          Администраторы ({usersByRole.admin.length})
                        </CardTitle>
                        <CardDescription>Администраторы системы</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>ФИО</TableHead>
                              <TableHead>Телефон</TableHead>
                              <TableHead>Дата регистрации</TableHead>
                              <TableHead>Статус</TableHead>
                              <TableHead>Действия</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {usersByRole.admin.map((u) => (
                              <TableRow key={u.id}>
                                <TableCell className="font-medium">{u.full_name}</TableCell>
                                <TableCell>{u.phone}</TableCell>
                                <TableCell>{new Date(u.created_at).toLocaleDateString('ru-RU')}</TableCell>
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
                  )}
                </div>
              )}

              {/* Управление складами */}
              {activeSection === 'warehouses' && (
                <div className="space-y-6">
                  {/* Создание склада */}
                  {activeTab === 'warehouses-create' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Plus className="mr-2 h-5 w-5" />
                          Создать новый склад
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleCreateWarehouse} className="space-y-4 max-w-md">
                          <div>
                            <Label htmlFor="warehouse_name">Имя склада</Label>
                            <Input
                              id="warehouse_name"
                              value={warehouseForm.name}
                              onChange={(e) => setWarehouseForm({...warehouseForm, name: e.target.value})}
                              placeholder="Например: Склад Москва-1"
                              required
                            />
                          </div>

                          <div>
                            <Label htmlFor="warehouse_location">Местоположение склада</Label>
                            <Input
                              id="warehouse_location"
                              value={warehouseForm.location}
                              onChange={(e) => setWarehouseForm({...warehouseForm, location: e.target.value})}
                              placeholder="Например: Москва, ул. Складская, 1"
                              required
                            />
                          </div>

                          <div>
                            <Label htmlFor="blocks_count">Количество блоков на складе (1-9)</Label>
                            <Select value={warehouseForm.blocks_count.toString()} onValueChange={(value) => setWarehouseForm({...warehouseForm, blocks_count: parseInt(value)})}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {[1,2,3,4,5,6,7,8,9].map(num => (
                                  <SelectItem key={num} value={num.toString()}>{num} блок{num > 1 ? (num < 5 ? 'а' : 'ов') : ''}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>

                          <div>
                            <Label htmlFor="shelves_per_block">Количество полок на каждом блоке (1-3)</Label>
                            <Select value={warehouseForm.shelves_per_block.toString()} onValueChange={(value) => setWarehouseForm({...warehouseForm, shelves_per_block: parseInt(value)})}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="1">1 полка</SelectItem>
                                <SelectItem value="2">2 полки</SelectItem>
                                <SelectItem value="3">3 полки</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div>
                            <Label htmlFor="cells_per_shelf">Количество ячеек на каждой полке</Label>
                            <Input
                              id="cells_per_shelf"
                              type="number"
                              min="1"
                              max="50"
                              value={warehouseForm.cells_per_shelf}
                              onChange={(e) => setWarehouseForm({...warehouseForm, cells_per_shelf: parseInt(e.target.value) || 1})}
                              required
                            />
                          </div>

                          <div className="bg-gray-50 p-4 rounded-lg">
                            <h4 className="font-medium mb-2">Параметры склада:</h4>
                            <div className="text-sm text-gray-600 space-y-1">
                              <p>Блоков: {warehouseForm.blocks_count}</p>
                              <p>Полок в блоке: {warehouseForm.shelves_per_block}</p>
                              <p>Ячеек на полке: {warehouseForm.cells_per_shelf}</p>
                              <p className="font-medium text-gray-900">
                                Общая вместимость: {warehouseForm.blocks_count * warehouseForm.shelves_per_block * warehouseForm.cells_per_shelf} ячеек
                              </p>
                            </div>
                          </div>

                          <Button type="submit" className="w-full">
                            <Plus className="mr-2 h-4 w-4" />
                            Создать склад
                          </Button>
                        </form>
                      </CardContent>
                    </Card>
                  )}

                  {/* Список складов */}
                  {(activeTab === 'warehouses-list' || !activeTab || activeTab === 'warehouses') && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Building className="mr-2 h-5 w-5" />
                            Список складов
                          </div>
                          <Button onClick={() => setActiveTab('warehouses-create')}>
                            <Plus className="mr-2 h-4 w-4" />
                            Создать склад
                          </Button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {warehouses.length === 0 ? (
                            <div className="text-center py-8">
                              <Building className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500 mb-4">Нет созданных складов</p>
                              <Button onClick={() => setActiveTab('warehouses-create')}>
                                <Plus className="mr-2 h-4 w-4" />
                                Создать первый склад
                              </Button>
                            </div>
                          ) : (
                            warehouses.map((warehouse) => (
                              <div key={warehouse.id} className="border rounded-lg p-4">
                                <div className="flex justify-between items-start mb-2">
                                  <div>
                                    <h3 className="font-semibold text-lg">{warehouse.name}</h3>
                                    <p className="text-gray-600">{warehouse.location}</p>
                                  </div>
                                  <Badge variant="default">Активен</Badge>
                                </div>
                                
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-blue-600">{warehouse.blocks_count}</div>
                                    <div className="text-sm text-gray-500">Блоков</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600">{warehouse.shelves_per_block}</div>
                                    <div className="text-sm text-gray-500">Полок/блок</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-purple-600">{warehouse.cells_per_shelf}</div>
                                    <div className="text-sm text-gray-500">Ячеек/полка</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-orange-600">{warehouse.total_capacity}</div>
                                    <div className="text-sm text-gray-500">Всего ячеек</div>
                                  </div>
                                </div>
                                
                                <div className="flex justify-between items-center mt-4 pt-4 border-t">
                                  <span className="text-sm text-gray-500">
                                    Создан: {new Date(warehouse.created_at).toLocaleDateString('ru-RU')}
                                  </span>
                                  <div className="flex space-x-2">
                                    <Button 
                                      size="sm" 
                                      variant="outline"
                                      onClick={() => handleOpenWarehouseLayout(warehouse)}
                                    >
                                      <Grid3X3 className="mr-2 h-4 w-4" />
                                      Управление
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Управление товарами на складе */}
                  {activeTab === 'warehouses-manage' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Package2 className="mr-2 h-5 w-5" />
                          Управление товарами на складе
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
                  )}
                </div>
              )}

              {/* Финансы (только для админа) */}
              {activeSection === 'finances' && user?.role === 'admin' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <DollarSign className="mr-2 h-5 w-5" />
                      Финансовый обзор
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-500">Раздел финансов в разработке</p>
                  </CardContent>
                </Card>
              )}

              {/* Отчеты */}
              {activeSection === 'reports' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <FileText className="mr-2 h-5 w-5" />
                      Отчеты
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-500">Раздел отчетов в разработке</p>
                  </CardContent>
                </Card>
              )}

              {/* Касса */}
              {activeSection === 'cashier' && (
                <div className="space-y-6">
                  {/* Приём оплаты */}
                  {activeTab === 'cashier-payment' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <CreditCard className="mr-2 h-5 w-5" />
                          Приём оплаты
                        </CardTitle>
                        <CardDescription>
                          Поиск груза по номеру и прием оплаты от клиента
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Button onClick={() => setPaymentModal(true)} className="mb-4">
                          <Plus className="mr-2 h-4 w-4" />
                          Принять оплату
                        </Button>
                      </CardContent>
                    </Card>
                  )}

                  {/* Не оплачено */}
                  {(activeTab === 'cashier-unpaid' || !activeTab || activeTab === 'cashier') && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Package className="mr-2 h-5 w-5" />
                            Не оплачено ({unpaidCargo.length})
                          </div>
                          <Button onClick={fetchUnpaidCargo}>
                            Обновить
                          </Button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {unpaidCargo.length === 0 ? (
                            <div className="text-center py-8">
                              <CheckCircle className="mx-auto h-12 w-12 text-green-500 mb-4" />
                              <p className="text-gray-500">Все грузы оплачены!</p>
                            </div>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Номер груза</TableHead>
                                  <TableHead>Отправитель</TableHead>
                                  <TableHead>Сумма к оплате</TableHead>
                                  <TableHead>Дата приема</TableHead>
                                  <TableHead>Действия</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {unpaidCargo.map((item) => (
                                  <TableRow key={item.id}>
                                    <TableCell className="font-medium">{item.cargo_number}</TableCell>
                                    <TableCell>
                                      <div>
                                        <div className="font-medium">{item.sender_full_name}</div>
                                        <div className="text-sm text-gray-500">{item.sender_phone}</div>
                                      </div>
                                    </TableCell>
                                    <TableCell className="font-bold text-red-600">{item.declared_value} ₽</TableCell>
                                    <TableCell>{new Date(item.created_at).toLocaleDateString('ru-RU')}</TableCell>
                                    <TableCell>
                                      <Button
                                        size="sm"
                                        onClick={() => {
                                          setPaymentForm({...paymentForm, cargo_number: item.cargo_number});
                                          setPaymentModal(true);
                                        }}
                                      >
                                        <CreditCard className="mr-2 h-4 w-4" />
                                        Принять оплату
                                      </Button>
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* История оплаты */}
                  {activeTab === 'cashier-history' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <FileText className="mr-2 h-5 w-5" />
                            История оплаты ({paymentHistory.length})
                          </div>
                          <Button onClick={fetchPaymentHistory}>
                            Обновить
                          </Button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {paymentHistory.length === 0 ? (
                            <div className="text-center py-8">
                              <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">История оплаты пуста</p>
                            </div>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Номер груза</TableHead>
                                  <TableHead>Клиент</TableHead>
                                  <TableHead>Сумма к оплате</TableHead>
                                  <TableHead>Оплачено</TableHead>
                                  <TableHead>Дата оплаты</TableHead>
                                  <TableHead>Кассир</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {paymentHistory.map((transaction) => (
                                  <TableRow key={transaction.id}>
                                    <TableCell className="font-medium">{transaction.cargo_number}</TableCell>
                                    <TableCell>
                                      <div>
                                        <div className="font-medium">{transaction.customer_name}</div>
                                        <div className="text-sm text-gray-500">{transaction.customer_phone}</div>
                                      </div>
                                    </TableCell>
                                    <TableCell>{transaction.amount_due} ₽</TableCell>
                                    <TableCell className="font-bold text-green-600">{transaction.amount_paid} ₽</TableCell>
                                    <TableCell>{new Date(transaction.payment_date).toLocaleDateString('ru-RU')} {new Date(transaction.payment_date).toLocaleTimeString('ru-RU')}</TableCell>
                                    <TableCell>{transaction.processed_by}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Логистика */}
              {activeSection === 'logistics' && (
                <div className="space-y-6">
                  {/* Приём машину */}
                  {activeTab === 'logistics-add-transport' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Plus className="mr-2 h-5 w-5" />
                          Приём машину
                        </CardTitle>
                        <CardDescription>
                          Добавить новый транспорт в систему логистики
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleCreateTransport} className="space-y-4 max-w-2xl">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <Label htmlFor="driver_name">ФИО водителя</Label>
                              <Input
                                id="driver_name"
                                value={transportForm.driver_name}
                                onChange={(e) => setTransportForm({...transportForm, driver_name: e.target.value})}
                                placeholder="Иванов Иван Иванович"
                                required
                              />
                            </div>
                            <div>
                              <Label htmlFor="driver_phone">Телефон водителя</Label>
                              <Input
                                id="driver_phone"
                                type="tel"
                                value={transportForm.driver_phone}
                                onChange={(e) => setTransportForm({...transportForm, driver_phone: e.target.value})}
                                placeholder="+79123456789"
                                required
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <Label htmlFor="transport_number">Номер транспорта</Label>
                              <Input
                                id="transport_number"
                                value={transportForm.transport_number}
                                onChange={(e) => setTransportForm({...transportForm, transport_number: e.target.value})}
                                placeholder="А123БВ77"
                                required
                              />
                            </div>
                            <div>
                              <Label htmlFor="capacity_kg">Объём допускаемых грузов (кг)</Label>
                              <Input
                                id="capacity_kg"
                                type="number"
                                step="0.1"
                                value={transportForm.capacity_kg}
                                onChange={(e) => setTransportForm({...transportForm, capacity_kg: e.target.value})}
                                placeholder="5000"
                                required
                              />
                            </div>
                          </div>

                          <div>
                            <Label htmlFor="direction">Направление</Label>
                            <Input
                              id="direction"
                              value={transportForm.direction}
                              onChange={(e) => setTransportForm({...transportForm, direction: e.target.value})}
                              placeholder="Москва - Душанбе"
                              required
                            />
                          </div>

                          <Button type="submit" className="w-full">
                            <Plus className="mr-2 h-4 w-4" />
                            Сохранить транспорт
                          </Button>
                        </form>
                      </CardContent>
                    </Card>
                  )}

                  {/* Список транспортов */}
                  {activeTab === 'logistics-transport-list' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Truck className="mr-2 h-5 w-5" />
                            Список транспортов ({transports.filter(t => t.status === 'empty' || t.status === 'filled').length})
                          </div>
                          <Button onClick={() => fetchTransports()}>
                            Обновить
                          </Button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {transports.filter(transport => transport.status === 'empty' || transport.status === 'filled').length === 0 ? (
                            <div className="col-span-full text-center py-8">
                              <Truck className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Нет доступных транспортов</p>
                            </div>
                          ) : (
                            transports.filter(transport => transport.status === 'empty' || transport.status === 'filled').map((transport) => (
                              <Card key={transport.id} className="p-4">
                                <div className="space-y-3">
                                  <div className="flex justify-between items-start">
                                    <h3 className="font-semibold text-lg">{transport.transport_number}</h3>
                                    <Badge variant={transport.status === 'empty' ? 'secondary' : 'default'}>
                                      {transport.status === 'empty' ? 'Пустой' : 'Заполнено'}
                                    </Badge>
                                  </div>
                                  
                                  <div className="space-y-2 text-sm">
                                    <p><strong>ФИО водителя:</strong> {transport.driver_name}</p>
                                    <p><strong>Телефон водителя:</strong> {transport.driver_phone}</p>
                                    <p><strong>Направление:</strong> {transport.direction}</p>
                                    <p><strong>Объём:</strong> {transport.current_load_kg} / {transport.capacity_kg} кг</p>
                                  </div>
                                  
                                  <Button 
                                    onClick={() => {
                                      setSelectedTransport(transport);
                                      fetchTransportCargoList(transport.id);
                                      fetchAvailableCargoForTransport();
                                      setTransportManagementModal(true);
                                    }}
                                    className="w-full"
                                    variant="outline"
                                  >
                                    Управление
                                  </Button>
                                </div>
                              </Card>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* В пути */}
                  {activeTab === 'logistics-in-transit' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Clock className="mr-2 h-5 w-5" />
                          Транспорт в пути ({transports.filter(t => t.status === 'in_transit').length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {transports.filter(transport => transport.status === 'in_transit').length === 0 ? (
                            <div className="text-center py-8">
                              <Clock className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Нет транспорта в пути</p>
                            </div>
                          ) : (
                            transports.filter(transport => transport.status === 'in_transit').map((transport) => (
                              <Card key={transport.id} className="p-4">
                                <div className="flex justify-between items-start">
                                  <div className="space-y-2">
                                    <h3 className="font-semibold text-lg">{transport.transport_number}</h3>
                                    <p className="text-sm text-gray-600"><strong>Водитель:</strong> {transport.driver_name}</p>
                                    <p className="text-sm text-gray-600"><strong>Направление:</strong> {transport.direction}</p>
                                    <p className="text-sm text-gray-600"><strong>Груз:</strong> {transport.current_load_kg} кг ({transport.cargo_list.length} мест)</p>
                                    <p className="text-sm text-gray-600"><strong>Отправлен:</strong> {new Date(transport.dispatched_at).toLocaleDateString('ru-RU')} {new Date(transport.dispatched_at).toLocaleTimeString('ru-RU')}</p>
                                  </div>
                                  <Badge className="bg-yellow-100 text-yellow-800">В пути</Badge>
                                </div>
                              </Card>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* На место назначения */}
                  {activeTab === 'logistics-arrived' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <MapPin className="mr-2 h-5 w-5" />
                          На место назначения ({transports.filter(t => t.status === 'arrived').length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {transports.filter(transport => transport.status === 'arrived').length === 0 ? (
                            <div className="text-center py-8">
                              <MapPin className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Нет транспорта на месте назначения</p>
                            </div>
                          ) : (
                            transports.filter(transport => transport.status === 'arrived').map((transport) => (
                              <Card key={transport.id} className="p-4">
                                <div className="flex justify-between items-start">
                                  <div className="space-y-2">
                                    <h3 className="font-semibold text-lg">{transport.transport_number}</h3>
                                    <p className="text-sm text-gray-600"><strong>Водитель:</strong> {transport.driver_name}</p>
                                    <p className="text-sm text-gray-600"><strong>Направление:</strong> {transport.direction}</p>
                                    <p className="text-sm text-gray-600"><strong>Груз:</strong> {transport.current_load_kg} кг ({transport.cargo_list.length} мест)</p>
                                  </div>
                                  <Badge className="bg-green-100 text-green-800">Прибыл</Badge>
                                </div>
                              </Card>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* История транспортировки */}
                  {activeTab === 'logistics-history' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <FileText className="mr-2 h-5 w-5" />
                          История транспортировки
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {transports.filter(transport => transport.status === 'completed').map((transport) => (
                            <Card key={transport.id} className="p-4 bg-gray-50">
                              <div className="space-y-2">
                                <div className="flex justify-between items-start">
                                  <h3 className="font-semibold text-lg">{transport.transport_number}</h3>
                                  <Badge variant="outline">Завершено</Badge>
                                </div>
                                <p className="text-sm text-gray-600"><strong>Водитель:</strong> {transport.driver_name}</p>
                                <p className="text-sm text-gray-600"><strong>Направление:</strong> {transport.direction}</p>
                                <p className="text-sm text-gray-600"><strong>Груз:</strong> {transport.current_load_kg} кг ({transport.cargo_list.length} мест)</p>
                                <p className="text-sm text-gray-600"><strong>Завершен:</strong> {transport.completed_at && new Date(transport.completed_at).toLocaleDateString('ru-RU')} {transport.completed_at && new Date(transport.completed_at).toLocaleTimeString('ru-RU')}</p>
                              </div>
                            </Card>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Уведомления */}
              {activeSection === 'notifications-management' && (
                <div className="space-y-6">
                  {/* Новые заявки */}
                  {(activeTab === 'notifications-requests' || !activeTab || activeTab === 'notifications-management') && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Bell className="mr-2 h-5 w-5" />
                            Новые заявки ({cargoRequests.length})
                          </div>
                          <Button onClick={fetchCargoRequests}>
                            Обновить
                          </Button>
                        </CardTitle>
                        <CardDescription>
                          Заявки от пользователей на отправку грузов
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {cargoRequests.length === 0 ? (
                            <div className="text-center py-8">
                              <Bell className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Новых заявок нет</p>
                            </div>
                          ) : (
                            cargoRequests.map((request) => (
                              <div key={request.id} className="border rounded-lg p-6 bg-blue-50">
                                <div className="flex justify-between items-start mb-4">
                                  <div>
                                    <h3 className="text-lg font-semibold text-blue-800">{request.request_number}</h3>
                                    <p className="text-sm text-gray-600">Подана: {new Date(request.created_at).toLocaleDateString('ru-RU')} {new Date(request.created_at).toLocaleTimeString('ru-RU')}</p>
                                  </div>
                                  <Badge variant="secondary">Новая заявка</Badge>
                                </div>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                  <div className="space-y-2">
                                    <h4 className="font-medium text-gray-900">Отправитель</h4>
                                    <div className="text-sm text-gray-600">
                                      <p><strong>ФИО:</strong> {request.sender_full_name}</p>
                                      <p><strong>Телефон:</strong> {request.sender_phone}</p>
                                      <p><strong>Адрес отправки:</strong> {request.pickup_address}</p>
                                    </div>
                                  </div>
                                  
                                  <div className="space-y-2">
                                    <h4 className="font-medium text-gray-900">Получатель</h4>
                                    <div className="text-sm text-gray-600">
                                      <p><strong>ФИО:</strong> {request.recipient_full_name}</p>
                                      <p><strong>Телефон:</strong> {request.recipient_phone}</p>
                                      <p><strong>Адрес получения:</strong> {request.recipient_address}</p>
                                    </div>
                                  </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                                  <div>
                                    <h4 className="font-medium text-gray-900">Информация о грузе</h4>
                                    <div className="text-sm text-gray-600">
                                      <p><strong>Название:</strong> {request.cargo_name}</p>
                                      <p><strong>Вес:</strong> {request.weight} кг</p>
                                      <p><strong>Стоимость:</strong> {request.declared_value} ₽</p>
                                    </div>
                                  </div>
                                  
                                  <div>
                                    <h4 className="font-medium text-gray-900">Маршрут</h4>
                                    <div className="text-sm text-gray-600">
                                      <p>{request.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}</p>
                                    </div>
                                  </div>
                                  
                                  <div>
                                    <h4 className="font-medium text-gray-900">Описание</h4>
                                    <div className="text-sm text-gray-600">
                                      <p>{request.description}</p>
                                    </div>
                                  </div>
                                </div>

                                <div className="flex space-x-3 pt-4 border-t">
                                  <Button
                                    onClick={() => handleAcceptRequest(request.id)}
                                    className="flex-1 bg-green-600 hover:bg-green-700"
                                  >
                                    <CheckCircle className="mr-2 h-4 w-4" />
                                    Принять заявку
                                  </Button>
                                  <Button
                                    variant="outline"
                                    onClick={() => {
                                      const reason = prompt('Причина отклонения (необязательно):');
                                      handleRejectRequest(request.id, reason || '');
                                    }}
                                    className="flex-1 text-red-600 border-red-300 hover:bg-red-50"
                                  >
                                    <X className="mr-2 h-4 w-4" />
                                    Отклонить
                                  </Button>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Системные уведомления */}
                  {activeTab === 'notifications-system' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Bell className="mr-2 h-5 w-5" />
                            Системные уведомления ({systemNotifications.length})
                          </div>
                          <Button onClick={fetchSystemNotifications}>
                            Обновить
                          </Button>
                        </CardTitle>
                        <CardDescription>
                          Уведомления об изменениях статусов грузов и операциях
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {systemNotifications.length === 0 ? (
                            <div className="text-center py-8">
                              <Bell className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Системных уведомлений нет</p>
                            </div>
                          ) : (
                            systemNotifications.map((notification) => (
                              <div
                                key={notification.id}
                                className={`border rounded-lg p-4 ${
                                  !notification.is_read ? 'bg-blue-50 border-blue-200' : 'bg-gray-50'
                                }`}
                              >
                                <div className="flex justify-between items-start">
                                  <div className="flex-1">
                                    <h4 className="font-semibold text-gray-900">{notification.title}</h4>
                                    <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                                    <div className="flex items-center mt-2 text-xs text-gray-500">
                                      <span>Тип: {
                                        notification.notification_type === 'request' ? 'Заявка' :
                                        notification.notification_type === 'cargo_status' ? 'Статус груза' :
                                        notification.notification_type === 'payment' ? 'Оплата' : 'Система'
                                      }</span>
                                      <span className="ml-4">
                                        {new Date(notification.created_at).toLocaleDateString('ru-RU')} {new Date(notification.created_at).toLocaleTimeString('ru-RU')}
                                      </span>
                                    </div>
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
                  )}
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Модальное окно приема оплаты */}
      <Dialog open={paymentModal} onOpenChange={setPaymentModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Приём оплаты</DialogTitle>
            <DialogDescription>
              Введите номер груза для поиска и приема оплаты
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="cargo_search">Номер груза</Label>
              <div className="flex space-x-2">
                <Input
                  id="cargo_search"
                  value={paymentForm.cargo_number}
                  onChange={(e) => setPaymentForm({...paymentForm, cargo_number: e.target.value})}
                  placeholder="Введите номер груза"
                />
                <Button onClick={handleSearchCargoForPayment}>
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {cargoForPayment && (
              <div className="border rounded-lg p-4 bg-gray-50">
                <h4 className="font-semibold mb-2">Информация о грузе:</h4>
                <div className="space-y-2 text-sm">
                  <p><strong>Номер:</strong> {cargoForPayment.cargo_number}</p>
                  <p><strong>Отправитель:</strong> {cargoForPayment.sender_full_name}</p>
                  <p><strong>Телефон:</strong> {cargoForPayment.sender_phone}</p>
                  <p><strong>Вес:</strong> {cargoForPayment.weight} кг</p>
                  <p><strong>Описание:</strong> {cargoForPayment.description}</p>
                  <p><strong>Сумма к оплате:</strong> <span className="text-red-600 font-bold">{cargoForPayment.declared_value} ₽</span></p>
                  <p><strong>Дата приема:</strong> {new Date(cargoForPayment.created_at).toLocaleDateString('ru-RU')} {new Date(cargoForPayment.created_at).toLocaleTimeString('ru-RU')}</p>
                </div>
              </div>
            )}

            {cargoForPayment && (
              <>
                <div>
                  <Label htmlFor="amount_paid">Сумма оплачена клиентом</Label>
                  <Input
                    id="amount_paid"
                    type="number"
                    step="0.01"
                    value={paymentForm.amount_paid}
                    onChange={(e) => setPaymentForm({...paymentForm, amount_paid: e.target.value})}
                    placeholder="Введите сумму"
                  />
                </div>

                <div>
                  <Label htmlFor="transaction_type">Способ оплаты</Label>
                  <Select value={paymentForm.transaction_type} onValueChange={(value) => setPaymentForm({...paymentForm, transaction_type: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">Наличными</SelectItem>
                      <SelectItem value="card">Картой</SelectItem>
                      <SelectItem value="transfer">Переводом</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="notes">Примечания (необязательно)</Label>
                  <Textarea
                    id="notes"
                    value={paymentForm.notes}
                    onChange={(e) => setPaymentForm({...paymentForm, notes: e.target.value})}
                    placeholder="Дополнительные заметки..."
                  />
                </div>

                <div className="flex space-x-2 pt-4">
                  <Button onClick={handleProcessPayment} className="flex-1">
                    <CreditCard className="mr-2 h-4 w-4" />
                    Оплатить
                  </Button>
                  <Button variant="outline" onClick={() => {
                    setPaymentModal(false);
                    setCargoForPayment(null);
                    setPaymentForm({cargo_number: '', amount_paid: '', transaction_type: 'cash', notes: ''});
                  }}>
                    Отмена
                  </Button>
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно схемы склада */}
      <Dialog open={layoutModal} onOpenChange={setLayoutModal}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              Схема склада: {selectedWarehouseForLayout?.name}
            </DialogTitle>
            <DialogDescription>
              Карта расположения блоков, полок и ячеек склада
            </DialogDescription>
          </DialogHeader>
          
          {warehouseLayout && (
            <div className="space-y-4">
              {/* Статистика */}
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded">
                  <div className="text-2xl font-bold text-blue-600">{warehouseLayout.statistics.total_cells}</div>
                  <div className="text-sm">Всего ячеек</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded">
                  <div className="text-2xl font-bold text-red-600">{warehouseLayout.statistics.occupied_cells}</div>
                  <div className="text-sm">Занято</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded">
                  <div className="text-2xl font-bold text-green-600">{warehouseLayout.statistics.available_cells}</div>
                  <div className="text-sm">Свободно</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-gray-600">{warehouseLayout.statistics.occupancy_rate}%</div>
                  <div className="text-sm">Заполненность</div>
                </div>
              </div>

              {/* Схема склада */}
              <div className="max-h-96 overflow-auto border rounded-lg p-4">
                <div className="space-y-6">
                  {Object.values(warehouseLayout.layout).map((block) => (
                    <div key={block.block_number} className="border rounded-lg p-4">
                      <h3 className="font-bold mb-3 text-center bg-gray-100 p-2 rounded">
                        Блок {block.block_number}
                      </h3>
                      <div className="space-y-4">
                        {Object.values(block.shelves).map((shelf) => (
                          <div key={shelf.shelf_number}>
                            <h4 className="font-semibold mb-2 text-sm bg-gray-50 p-1 rounded">
                              Полка {shelf.shelf_number}
                            </h4>
                            <div className="grid grid-cols-5 gap-2">
                              {shelf.cells.map((cell) => (
                                <div
                                  key={cell.id}
                                  className={`p-2 text-xs text-center rounded border-2 ${
                                    cell.is_occupied 
                                      ? 'bg-red-100 border-red-300 text-red-800' 
                                      : 'bg-green-100 border-green-300 text-green-800'
                                  }`}
                                  title={cell.cargo_info ? `${cell.cargo_info.cargo_number} - ${cell.cargo_info.sender_name}` : 'Свободная ячейка'}
                                >
                                  <div className="font-bold">Я{cell.cell_number}</div>
                                  {cell.cargo_info && (
                                    <div className="mt-1">
                                      <div className="font-semibold">{cell.cargo_info.cargo_number}</div>
                                      <div>{cell.cargo_info.weight}кг</div>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-center space-x-4 text-sm">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-green-100 border-2 border-green-300 rounded mr-2"></div>
                  <span>Свободная ячейка</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-red-100 border-2 border-red-300 rounded mr-2"></div>
                  <span>Занятая ячейка</span>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Модальное окно управления транспортом */}
      <Dialog open={transportManagementModal} onOpenChange={setTransportManagementModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Управление транспортом {selectedTransport?.transport_number}
            </DialogTitle>
            <DialogDescription>
              Выберите функцию для управления транспортом
            </DialogDescription>
          </DialogHeader>
          
          {selectedTransport && (
            <div className="space-y-6">
              {/* Информация о транспорте */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">Информация о транспорте</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <p><strong>Номер:</strong> {selectedTransport.transport_number}</p>
                  <p><strong>Водитель:</strong> {selectedTransport.driver_name}</p>
                  <p><strong>Телефон:</strong> {selectedTransport.driver_phone}</p>
                  <p><strong>Направление:</strong> {selectedTransport.direction}</p>
                  <p><strong>Вместимость:</strong> {selectedTransport.capacity_kg} кг</p>
                  <p><strong>Загрузка:</strong> {selectedTransport.current_load_kg} кг ({Math.round((selectedTransport.current_load_kg / selectedTransport.capacity_kg) * 100)}%)</p>
                </div>
              </div>

              {/* Функции управления */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Размещение груза */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-3">Размещение груза</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Разместить груз со склада на транспорт
                  </p>
                  
                  {/* Доступные грузы */}
                  <div className="mb-4">
                    <Label>Доступные грузы на складе:</Label>
                    <div className="max-h-40 overflow-y-auto border rounded mt-2">
                      {availableCargoForTransport.length === 0 ? (
                        <p className="p-3 text-gray-500 text-sm">Нет доступных грузов</p>
                      ) : (
                        availableCargoForTransport.map((cargo) => (
                          <div key={cargo.id} className="p-2 border-b flex items-center">
                            <input
                              type="checkbox"
                              checked={selectedCargoForPlacement.includes(cargo.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedCargoForPlacement([...selectedCargoForPlacement, cargo.id]);
                                } else {
                                  setSelectedCargoForPlacement(selectedCargoForPlacement.filter(id => id !== cargo.id));
                                }
                              }}
                              className="mr-2"
                            />
                            <div className="flex-1 text-sm">
                              <p><strong>{cargo.cargo_number}</strong> - {cargo.weight} кг</p>
                              <p className="text-gray-500">{cargo.description}</p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  
                  <Button 
                    onClick={() => handlePlaceCargoOnTransport(selectedTransport.id, selectedCargoForPlacement)}
                    disabled={selectedCargoForPlacement.length === 0}
                    className="w-full"
                  >
                    Разместить выбранные грузы
                  </Button>
                </Card>

                {/* Список размещенных грузов */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-3">Список размещенных грузов</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Общий объём: {transportCargoList.total_weight || 0} кг
                  </p>
                  
                  <div className="max-h-40 overflow-y-auto border rounded">
                    {!transportCargoList.cargo_list || transportCargoList.cargo_list.length === 0 ? (
                      <p className="p-3 text-gray-500 text-sm">Груз не размещен</p>
                    ) : (
                      transportCargoList.cargo_list.map((cargo) => (
                        <div key={cargo.id} className="p-2 border-b text-sm">
                          <p><strong>{cargo.cargo_number}</strong> - {cargo.weight} кг</p>
                          <p className="text-gray-500">{cargo.description}</p>
                          <p className="text-gray-500">Получатель: {cargo.recipient_name}</p>
                        </div>
                      ))
                    )}
                  </div>
                </Card>

                {/* Отправить транспорт */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-3">Отправить транспорт</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Отправить транспорт в место назначения. Пользователи получат уведомления.
                  </p>
                  <Button 
                    onClick={() => handleDispatchTransport(selectedTransport.id)}
                    disabled={selectedTransport.status !== 'filled'}
                    className="w-full"
                    variant={selectedTransport.status === 'filled' ? 'default' : 'secondary'}
                  >
                    {selectedTransport.status === 'filled' ? 'Отправить транспорт' : 'Транспорт должен быть заполнен'}
                  </Button>
                </Card>

                {/* Удалить транспорт */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-3">Удалить транспорт</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Удалить транспорт и переместить в историю
                  </p>
                  <Button 
                    onClick={() => handleDeleteTransport(selectedTransport.id)}
                    variant="destructive"
                    className="w-full"
                  >
                    Удалить транспорт
                  </Button>
                </Card>

              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

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