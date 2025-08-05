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
  DollarSign, FileText, Grid3X3, Package2, Home, CreditCard, Printer, Zap, MessageCircle,
  QrCode, Camera, Download
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
  const [registerForm, setRegisterForm] = useState({ full_name: '', phone: '', password: '' }); // Убрана роль (Функция 3)
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
    cargo_name: '',
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

  // Search and header states
  const [searchType, setSearchType] = useState('all');
  const [showSearchResults, setShowSearchResults] = useState(false);

  // Operator-warehouse management states
  const [operatorWarehouseBindings, setOperatorWarehouseBindings] = useState([]);
  const [operatorBindingModal, setOperatorBindingModal] = useState(false);
  const [selectedOperatorForBinding, setSelectedOperatorForBinding] = useState('');
  const [selectedWarehouseForBinding, setSelectedWarehouseForBinding] = useState('');

  // Warehouse cell management states
  const [selectedCellCargo, setSelectedCellCargo] = useState(null);
  const [cargoDetailModal, setCargoDetailModal] = useState(false);
  const [cargoEditModal, setCargoEditModal] = useState(false);
  const [cargoMoveModal, setCargoMoveModal] = useState(false);
  const [editingCargo, setEditingCargo] = useState(null);
  const [cargoEditForm, setCargoEditForm] = useState({});
  const [cargoMoveForm, setCargoMoveForm] = useState({
    warehouse_id: '',
    block_number: '',
    shelf_number: '',
    cell_number: ''
  });

  // QR Code states
  const [qrScannerModal, setQrScannerModal] = useState(false);
  const [qrPrintModal, setQrPrintModal] = useState(false);
  const [selectedCargoForQr, setSelectedCargoForQr] = useState(null);
  const [selectedWarehouseForQr, setSelectedWarehouseForQr] = useState(null);
  const [qrScanResult, setQrScanResult] = useState(null);

  // Arrived transport and cargo placement states
  const [arrivedTransports, setArrivedTransports] = useState([]);
  const [selectedArrivedTransport, setSelectedArrivedTransport] = useState(null);
  const [arrivedTransportModal, setArrivedTransportModal] = useState(false);
  const [arrivedCargoList, setArrivedCargoList] = useState([]);
  const [cargoPlacementModal, setCargoPlacementModal] = useState(false);
  const [selectedCargoForWarehouse, setSelectedCargoForWarehouse] = useState(null);
  const [placementForm, setPlacementForm] = useState({
    warehouse_id: '',
    block_number: 1,
    shelf_number: 1,
    cell_number: 1
  });

  // Transport visualization states
  const [transportVisualizationModal, setTransportVisualizationModal] = useState(false);
  const [selectedTransportForVisualization, setSelectedTransportForVisualization] = useState(null);
  const [transportVisualizationData, setTransportVisualizationData] = useState(null);

  // QR/Number cargo placement states
  const [qrPlacementModal, setQrPlacementModal] = useState(false);
  const [qrPlacementForm, setQrPlacementForm] = useState({
    cargo_number: '',
    qr_data: '',
    cell_qr_data: '',
    block_number: 1,
    shelf_number: 1,
    cell_number: 1
  });

  // Operator-specific states
  const [operatorWarehouses, setOperatorWarehouses] = useState([]);
  const [interwarehouseTransportModal, setInterwarehouseTransportModal] = useState(false);
  const [interwarehouseForm, setInterwarehouseForm] = useState({
    source_warehouse_id: '',
    destination_warehouse_id: '',
    driver_name: '',
    driver_phone: '',
    capacity_kg: 1000
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
        fetchOperatorCargo();
        fetchUsersByRole();
        fetchUnpaidCargo();
        fetchPaymentHistory();
        fetchCargoRequests();
        fetchSystemNotifications();
        fetchTransports();
        fetchOperatorWarehouseBindings();
      } else if (user.role === 'warehouse_operator') {
        fetchWarehouseCargo();
        fetchWarehouses();
        fetchOperatorCargo();
        fetchUnpaidCargo();
        fetchPaymentHistory();
        fetchCargoRequests();
        fetchSystemNotifications();
        fetchTransportsList(); // Обновлено для операторов
        fetchArrivedTransports();
        fetchOperatorWarehouses(); // Добавлено для операторов
      } else {
        fetchMyCargo();
        fetchMyRequests();
        fetchSystemNotifications();
      }
    }
  }, [user]);

  const fetchUserData = async () => {
    try {
      // Get user data from backend using the token
      const userData = await apiCall('/api/auth/me', 'GET');
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      // Token is invalid, clear it
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

  const handlePlaceCargoOnTransport = async (transportId, cargoNumbers) => {
    try {
      if (!cargoNumbers || cargoNumbers.length === 0) {
        showAlert('Не указаны номера грузов для размещения', 'error');
        return;
      }

      // Отправляем номера грузов напрямую, без преобразования в ID
      await apiCall(`/api/transport/${transportId}/place-cargo`, 'POST', {
        transport_id: transportId,
        cargo_numbers: cargoNumbers
      });
      
      showAlert(`Груз успешно размещен на транспорте! (${cargoNumbers.length} мест)`, 'success');
      fetchTransports();
      fetchTransportCargoList(transportId);
      fetchAvailableCargoForTransport(); // Обновить список доступных грузов
      setSelectedCargoForPlacement([]);
    } catch (error) {
      console.error('Place cargo on transport error:', error);
      // Показать более подробную ошибку пользователю
      const errorMessage = error.response?.data?.detail || error.message || 'Ошибка размещения груза';
      showAlert(errorMessage, 'error');
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

  // Search functions
  const handleSearch = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    try {
      const results = await apiCall(`/api/cargo/search?query=${encodeURIComponent(query)}&search_type=${searchType}`);
      setSearchResults(results || []);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setShowSearchResults(false);
  };

  // Operator-warehouse binding functions
  const fetchOperatorWarehouseBindings = async () => {
    try {
      const data = await apiCall('/api/admin/operator-warehouse-bindings');
      setOperatorWarehouseBindings(data);
    } catch (error) {
      console.error('Error fetching operator-warehouse bindings:', error);
    }
  };

  const handleCreateOperatorBinding = async () => {
    if (!selectedOperatorForBinding || !selectedWarehouseForBinding) {
      showAlert('Выберите оператора и склад для привязки', 'error');
      return;
    }

    try {
      await apiCall('/api/admin/operator-warehouse-binding', 'POST', {
        operator_id: selectedOperatorForBinding,
        warehouse_id: selectedWarehouseForBinding
      });
      showAlert('Привязка оператора к складу создана успешно!', 'success');
      setOperatorBindingModal(false);
      setSelectedOperatorForBinding('');
      setSelectedWarehouseForBinding('');
      fetchOperatorWarehouseBindings();
    } catch (error) {
      console.error('Create operator binding error:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка создания привязки';
      showAlert(errorMessage, 'error');
    }
  };

  // Warehouse cell and cargo detail functions
  const handleCellClick = async (warehouseId, locationCode) => {
    try {
      const cargoData = await apiCall(`/api/warehouse/${warehouseId}/cell/${locationCode}/cargo`);
      setSelectedCellCargo(cargoData);
      setCargoDetailModal(true);
    } catch (error) {
      if (error.response?.status === 404) {
        showAlert('В этой ячейке нет груза', 'info');
      } else {
        console.error('Error fetching cell cargo:', error);
        showAlert('Ошибка получения информации о грузе', 'error');
      }
    }
  };

  const fetchCargoDetails = async (cargoId) => {
    try {
      const cargoData = await apiCall(`/api/cargo/${cargoId}/details`);
      return cargoData;
    } catch (error) {
      console.error('Error fetching cargo details:', error);
      throw error;
    }
  };

  const handleEditCargo = (cargo) => {
    setEditingCargo(cargo);
    setCargoEditForm({
      cargo_name: cargo.cargo_name || '',
      description: cargo.description || '',
      weight: cargo.weight || '',
      declared_value: cargo.declared_value || '',
      sender_full_name: cargo.sender_full_name || '',
      sender_phone: cargo.sender_phone || '',
      recipient_full_name: cargo.recipient_full_name || cargo.recipient_name || '',
      recipient_phone: cargo.recipient_phone || '',
      recipient_address: cargo.recipient_address || ''
    });
    setCargoEditModal(true);
  };

  const handleUpdateCargo = async () => {
    if (!editingCargo) return;

    try {
      await apiCall(`/api/cargo/${editingCargo.id}/update`, 'PUT', cargoEditForm);
      showAlert('Информация о грузе обновлена!', 'success');
      setCargoEditModal(false);
      setEditingCargo(null);
      
      // Обновить данные
      if (selectedCellCargo && selectedCellCargo.id === editingCargo.id) {
        const updatedCargo = await fetchCargoDetails(editingCargo.id);
        setSelectedCellCargo(updatedCargo);
      }
      
      // Обновить списки грузов
      fetchOperatorCargo();
      fetchAllCargo();
    } catch (error) {
      console.error('Update cargo error:', error);
    }
  };

  const handleMoveCargo = (cargo) => {
    setEditingCargo(cargo);
    setCargoMoveForm({
      warehouse_id: cargo.warehouse_id || '',
      block_number: cargo.block_number || '',
      shelf_number: cargo.shelf_number || '',
      cell_number: cargo.cell_number || ''
    });
    setCargoMoveModal(true);
  };

  const handleMoveCargoSubmit = async () => {
    if (!editingCargo) return;

    try {
      await apiCall(`/api/warehouse/cargo/${editingCargo.id}/move`, 'POST', cargoMoveForm);
      showAlert('Груз успешно перемещен!', 'success');
      setCargoMoveModal(false);
      setEditingCargo(null);
      
      // Обновить данные
      fetchOperatorCargo();
      setCargoDetailModal(false);
    } catch (error) {
      console.error('Move cargo error:', error);
      const errorMessage = error.response?.data?.detail || 'Ошибка перемещения груза';
      showAlert(errorMessage, 'error');
    }
  };

  const handleRemoveCargoFromCell = async (cargo) => {
    if (window.confirm(`Вы уверены, что хотите удалить груз ${cargo.cargo_number} из ячейки?`)) {
      try {
        await apiCall(`/api/warehouse/cargo/${cargo.id}/remove`, 'DELETE');
        showAlert('Груз удален из ячейки!', 'success');
        setCargoDetailModal(false);
        fetchOperatorCargo();
      } catch (error) {
        console.error('Remove cargo error:', error);
      }
    }
  };

  // Print transport cargo list
  const printTransportCargoList = (transport, cargoList) => {
    const printWindow = window.open('', '_blank');
    const totalWeight = cargoList.reduce((sum, cargo) => sum + cargo.weight, 0);
    
    printWindow.document.write(`
      <html>
        <head>
          <title>Список грузов - ${transport.transport_number}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; font-size: 12px; }
            .header { text-align: center; margin-bottom: 20px; }
            .logo { font-size: 24px; font-weight: bold; color: #1f2937; margin-bottom: 10px; }
            .company { font-size: 18px; margin-bottom: 5px; }
            .title { font-size: 16px; font-weight: bold; margin: 20px 0; }
            .info-section { margin-bottom: 15px; padding: 10px; border: 1px solid #ccc; }
            .info-title { font-weight: bold; margin-bottom: 5px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .summary { margin-top: 20px; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd; }
            .footer { margin-top: 30px; text-align: center; font-size: 10px; color: #666; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">📦 TAJLINE.TJ</div>
            <div class="company">ООО "Таджлайн"</div>
            <div class="title">СПИСОК ГРУЗОВ НА ТРАНСПОРТЕ</div>
          </div>

          <div class="info-section">
            <div class="info-title">Информация о транспорте</div>
            <p><strong>Номер транспорта:</strong> ${transport.transport_number}</p>
            <p><strong>Водитель:</strong> ${transport.driver_name}</p>
            <p><strong>Телефон водителя:</strong> ${transport.driver_phone}</p>
            <p><strong>Направление:</strong> ${transport.direction}</p>
            <p><strong>Вместимость:</strong> ${transport.capacity_kg} кг</p>
            <p><strong>Дата формирования:</strong> ${new Date().toLocaleDateString('ru-RU')} ${new Date().toLocaleTimeString('ru-RU')}</p>
          </div>

          <table>
            <thead>
              <tr>
                <th>№</th>
                <th>Номер груза</th>
                <th>Название</th>
                <th>Вес (кг)</th>
                <th>Отправитель</th>
                <th>Получатель</th>
                <th>Телефон получателя</th>
                <th>Адрес доставки</th>
              </tr>
            </thead>
            <tbody>
              ${cargoList.map((cargo, index) => `
                <tr>
                  <td>${index + 1}</td>
                  <td><strong>${cargo.cargo_number}</strong></td>
                  <td>${cargo.cargo_name || 'Груз'}</td>
                  <td>${cargo.weight}</td>
                  <td>${cargo.sender_full_name || 'Не указан'}<br><small>${cargo.sender_phone || ''}</small></td>
                  <td>${cargo.recipient_full_name || cargo.recipient_name}</td>
                  <td>${cargo.recipient_phone || 'Не указан'}</td>
                  <td>${cargo.recipient_address || 'Не указан'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <div class="summary">
            <p><strong>Всего грузов:</strong> ${cargoList.length} мест</p>
            <p><strong>Общий вес:</strong> ${totalWeight} кг</p>
            <p><strong>Заполненность транспорта:</strong> ${Math.round((totalWeight / transport.capacity_kg) * 100)}%</p>
            <p><strong>Остаток вместимости:</strong> ${transport.capacity_kg - totalWeight} кг</p>
          </div>

          <div class="footer">
            <p>Этот документ сформирован автоматически системой TAJLINE.TJ</p>
            <p>Дата и время: ${new Date().toLocaleDateString('ru-RU')} ${new Date().toLocaleTimeString('ru-RU')}</p>
          </div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
  };

  // Print invoice for individual cargo
  const printInvoice = (cargo) => {
    const printWindow = window.open('', '_blank');
    
    printWindow.document.write(`
      <html>
        <head>
          <title>Накладная - ${cargo.cargo_number}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; font-size: 14px; }
            .header { text-align: center; margin-bottom: 30px; }
            .logo { font-size: 28px; font-weight: bold; color: #1f2937; margin-bottom: 10px; }
            .company { font-size: 20px; margin-bottom: 5px; }
            .title { font-size: 18px; font-weight: bold; margin: 20px 0; border-bottom: 2px solid #333; padding-bottom: 10px; }
            .info-section { margin-bottom: 20px; padding: 15px; border: 2px solid #333; }
            .info-title { font-weight: bold; font-size: 16px; margin-bottom: 10px; background-color: #f0f0f0; padding: 5px; }
            .info-row { display: flex; justify-content: space-between; margin-bottom: 8px; padding: 5px 0; border-bottom: 1px dotted #ccc; }
            .info-label { font-weight: bold; width: 40%; }
            .info-value { width: 60%; }
            .summary-box { padding: 15px; background-color: #f9f9f9; border: 2px solid #333; margin-top: 20px; }
            .footer { margin-top: 40px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #ccc; padding-top: 10px; }
            .signatures { margin-top: 30px; display: flex; justify-content: space-between; }
            .signature-block { width: 45%; text-align: center; padding: 20px 0; border-top: 1px solid #333; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">📦 TAJLINE.TJ</div>
            <div class="company">ООО "Таджлайн"</div>
            <div class="title">ТОВАРНАЯ НАКЛАДНАЯ № ${cargo.cargo_number}</div>
          </div>

          <div class="info-section">
            <div class="info-title">Информация о грузе</div>
            <div class="info-row">
              <span class="info-label">Номер груза:</span>
              <span class="info-value"><strong>${cargo.cargo_number}</strong></span>
            </div>
            <div class="info-row">
              <span class="info-label">Наименование:</span>
              <span class="info-value">${cargo.cargo_name || cargo.description || 'Не указано'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Вес:</span>
              <span class="info-value">${cargo.weight} кг</span>
            </div>
            <div class="info-row">
              <span class="info-label">Объявленная стоимость:</span>
              <span class="info-value">${cargo.declared_value} руб.</span>
            </div>
            <div class="info-row">
              <span class="info-label">Статус:</span>
              <span class="info-value">${cargo.status === 'accepted' ? 'Принят' : cargo.status === 'in_warehouse' ? 'На складе' : cargo.status === 'in_transit' ? 'В пути' : cargo.status === 'delivered' ? 'Доставлен' : cargo.status}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Маршрут:</span>
              <span class="info-value">${cargo.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : cargo.route}</span>
            </div>
          </div>

          <div class="info-section">
            <div class="info-title">Отправитель</div>
            <div class="info-row">
              <span class="info-label">ФИО:</span>
              <span class="info-value">${cargo.sender_full_name || 'Не указано'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Телефон:</span>
              <span class="info-value">${cargo.sender_phone || 'Не указан'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Адрес:</span>
              <span class="info-value">${cargo.sender_address || 'Не указан'}</span>
            </div>
          </div>

          <div class="info-section">
            <div class="info-title">Получатель</div>
            <div class="info-row">
              <span class="info-label">ФИО:</span>
              <span class="info-value">${cargo.recipient_full_name || cargo.recipient_name || 'Не указано'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Телефон:</span>
              <span class="info-value">${cargo.recipient_phone || 'Не указан'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Адрес доставки:</span>
              <span class="info-value">${cargo.recipient_address || 'Не указан'}</span>
            </div>
          </div>

          ${cargo.warehouse_location ? `
          <div class="info-section">
            <div class="info-title">Информация о размещении</div>
            <div class="info-row">
              <span class="info-label">Склад:</span>
              <span class="info-value">${cargo.warehouse_location}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Ячейка:</span>
              <span class="info-value">Блок ${cargo.block_number}, Полка ${cargo.shelf_number}, Ячейка ${cargo.cell_number}</span>
            </div>
          </div>
          ` : ''}

          ${cargo.created_by_operator ? `
          <div class="info-section">
            <div class="info-title">Информация об операторах</div>
            <div class="info-row">
              <span class="info-label">Принял груз:</span>
              <span class="info-value">${cargo.created_by_operator}</span>
            </div>
            ${cargo.placed_by_operator ? `
            <div class="info-row">
              <span class="info-label">Разместил на складе:</span>
              <span class="info-value">${cargo.placed_by_operator}</span>
            </div>
            ` : ''}
          </div>
          ` : ''}

          <div class="summary-box">
            <div class="info-row">
              <span class="info-label">Дата создания накладной:</span>
              <span class="info-value">${new Date().toLocaleDateString('ru-RU')} ${new Date().toLocaleTimeString('ru-RU')}</span>
            </div>
            <div class="info-row">
              <span class="info-label">К доплате при получении:</span>
              <span class="info-value"><strong>${cargo.declared_value} руб.</strong></span>
            </div>
          </div>

          <div class="signatures">
            <div class="signature-block">
              <div>Подпись отправителя</div>
              <div style="margin-top: 10px;">_________________</div>
            </div>
            <div class="signature-block">
              <div>Подпись получателя</div>
              <div style="margin-top: 10px;">_________________</div>
            </div>
          </div>

          <div class="footer">
            <p>Этот документ сформирован автоматически системой TAJLINE.TJ</p>
            <p>Адрес: г. Москва, ул. Транспортная, д. 1 | Телефон: +7 (495) 123-45-67</p>
            <p>Дата и время: ${new Date().toLocaleDateString('ru-RU')} ${new Date().toLocaleTimeString('ru-RU')}</p>
          </div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
  };

  const handleDeleteOperatorBinding = async (bindingId) => {
    if (window.confirm('Вы уверены, что хотите удалить эту привязку?')) {
      try {
        await apiCall(`/api/admin/operator-warehouse-binding/${bindingId}`, 'DELETE');
        showAlert('Привязка удалена успешно!', 'success');
        fetchOperatorWarehouseBindings();
      } catch (error) {
        console.error('Delete operator binding error:', error);
      }
    }
  };

  // QR Code functions
  const getCargoQrCode = async (cargoId) => {
    try {
      const data = await apiCall(`/api/cargo/${cargoId}/qr-code`);
      return data.qr_code;
    } catch (error) {
      console.error('Error getting cargo QR code:', error);
      return null;
    }
  };

  const getCellQrCode = async (warehouseId, block, shelf, cell) => {
    try {
      const data = await apiCall(`/api/warehouse/${warehouseId}/cell-qr/${block}/${shelf}/${cell}`);
      return data.qr_code;
    } catch (error) {
      console.error('Error getting cell QR code:', error);
      return null;
    }
  };

  const handleQrScan = async (qrText) => {
    try {
      const data = await apiCall('/api/qr/scan', 'POST', { qr_text: qrText });
      setQrScanResult(data);
      setQrScannerModal(false);
      showAlert('QR код успешно отсканирован!', 'success');
    } catch (error) {
      console.error('QR scan error:', error);
      setQrScanResult(null);
    }
  };

  const printCargoQrLabel = async (cargo) => {
    try {
      const qrCode = await getCargoQrCode(cargo.id);
      if (!qrCode) {
        showAlert('Не удалось получить QR код', 'error');
        return;
      }

      const printWindow = window.open('', '_blank');
      printWindow.document.write(`
        <html>
          <head>
            <title>QR Этикетка - ${cargo.cargo_number}</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20px; text-align: center; }
              .qr-label { border: 2px solid #000; padding: 20px; margin: 20px auto; width: 300px; }
              .qr-code { margin: 20px 0; }
              .cargo-info { font-size: 14px; font-weight: bold; margin: 10px 0; }
              .cargo-details { font-size: 12px; margin: 5px 0; }
            </style>
          </head>
          <body>
            <div class="qr-label">
              <h3>TAJLINE.TJ</h3>
              <div class="cargo-info">ГРУЗ №${cargo.cargo_number}</div>
              <div class="qr-code">
                <img src="${qrCode}" alt="QR Code" style="width: 150px; height: 150px;" />
              </div>
              <div class="cargo-details">
                <div><strong>Наименование:</strong> ${cargo.cargo_name || 'Груз'}</div>
                <div><strong>Вес:</strong> ${cargo.weight} кг</div>
                <div><strong>Получатель:</strong> ${cargo.recipient_full_name || cargo.recipient_name}</div>
              </div>
            </div>
          </body>
        </html>
      `);
      
      printWindow.document.close();
      printWindow.print();
    } catch (error) {
      console.error('Error printing QR label:', error);
    }
  };

  const printWarehouseCellsQr = async (warehouse) => {
    try {
      const data = await apiCall(`/api/warehouse/${warehouse.id}/all-cells-qr`);
      
      const printWindow = window.open('', '_blank');
      printWindow.document.write(`
        <html>
          <head>
            <title>QR Коды ячеек - ${data.warehouse_name}</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 10px; }
              .header { text-align: center; margin-bottom: 20px; }
              .qr-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
              .qr-cell { border: 1px solid #ccc; padding: 10px; text-align: center; page-break-inside: avoid; }
              .qr-code { margin: 10px 0; }
              .cell-info { font-size: 12px; font-weight: bold; }
              @media print { .qr-grid { grid-template-columns: repeat(3, 1fr); } }
            </style>
          </head>
          <body>
            <div class="header">
              <h2>QR Коды ячеек склада "${data.warehouse_name}"</h2>
              <p>Всего ячеек: ${data.total_cells}</p>
            </div>
            <div class="qr-grid">
              ${data.qr_codes.map(cell => `
                <div class="qr-cell">
                  <div class="cell-info">${cell.location}</div>
                  <div class="qr-code">
                    <img src="${cell.qr_code}" alt="QR Code" style="width: 80px; height: 80px;" />
                  </div>
                  <div class="cell-info">${data.warehouse_name}</div>
                </div>
              `).join('')}
            </div>
          </body>
        </html>
      `);
      
      printWindow.document.close();
      printWindow.print();
    } catch (error) {
      console.error('Error printing warehouse QR codes:', error);
    }
  };

  // Arrived Transport Functions
  const fetchArrivedTransports = async () => {
    try {
      const data = await apiCall('/api/transport/arrived');
      setArrivedTransports(data);
    } catch (error) {
      console.error('Error fetching arrived transports:', error);
    }
  };

  const fetchArrivedTransportCargo = async (transportId) => {
    try {
      const data = await apiCall(`/api/transport/${transportId}/arrived-cargo`);
      setArrivedCargoList(data);
    } catch (error) {
      console.error('Error fetching arrived cargo:', error);
    }
  };

  const handleMarkTransportArrived = async (transportId) => {
    if (window.confirm('Отметить транспорт как прибывший?')) {
      try {
        await apiCall(`/api/transport/${transportId}/arrive`, 'POST');
        showAlert('Транспорт отмечен как прибывший!', 'success');
        fetchTransports();
        fetchArrivedTransports();
      } catch (error) {
        console.error('Error marking transport as arrived:', error);
        showAlert('Ошибка при отметке транспорта как прибывшего', 'error');
      }
    }
  };

  const handlePlaceCargoFromTransport = async (e) => {
    e.preventDefault();
    try {
      const placementData = {
        cargo_id: selectedCargoForWarehouse.id,
        warehouse_id: placementForm.warehouse_id,
        block_number: parseInt(placementForm.block_number),
        shelf_number: parseInt(placementForm.shelf_number),
        cell_number: parseInt(placementForm.cell_number)
      };

      const response = await apiCall(`/api/transport/${selectedArrivedTransport.id}/place-cargo-to-warehouse`, 'POST', placementData);
      
      showAlert(`Груз ${response.cargo_number} успешно размещен на складе ${response.warehouse_name} в ячейке ${response.location}!`, 'success');
      
      // Обновить данные
      fetchArrivedTransportCargo(selectedArrivedTransport.id);
      fetchArrivedTransports();
      
      // Закрыть модал и сбросить форму
      setCargoPlacementModal(false);
      setSelectedCargoForWarehouse(null);
      setPlacementForm({
        warehouse_id: '',
        block_number: 1,
        shelf_number: 1,
        cell_number: 1
      });
      
      if (response.transport_status === 'completed') {
        showAlert('Все грузы размещены! Транспорт завершен.', 'info');
        setArrivedTransportModal(false);
      }
    } catch (error) {
      console.error('Error placing cargo:', error);
      showAlert('Ошибка размещения груза на складе', 'error');
    }
  };

  // Transport Visualization Functions
  const fetchTransportVisualization = async (transportId) => {
    try {
      const data = await apiCall(`/api/transport/${transportId}/visualization`);
      setTransportVisualizationData(data);
    } catch (error) {
      console.error('Error fetching transport visualization:', error);
    }
  };

  const openTransportVisualization = (transport) => {
    setSelectedTransportForVisualization(transport);
    fetchTransportVisualization(transport.id);
    setTransportVisualizationModal(true);
  };

  // QR/Number Cargo Placement Functions
  const handleQrCargoPlacement = async (e) => {
    e.preventDefault();
    try {
      const placementData = {
        cargo_number: qrPlacementForm.cargo_number,
        qr_data: qrPlacementForm.qr_data,
        cell_qr_data: qrPlacementForm.cell_qr_data,
        block_number: parseInt(qrPlacementForm.block_number),
        shelf_number: parseInt(qrPlacementForm.shelf_number),
        cell_number: parseInt(qrPlacementForm.cell_number)
      };

      const response = await apiCall(`/api/transport/${selectedArrivedTransport.id}/place-cargo-by-number`, 'POST', placementData);
      
      showAlert(
        `Груз ${response.cargo_number} размещен на складе ${response.warehouse_name} в ячейке ${response.location}! ${response.warehouse_auto_selected ? 'Склад выбран автоматически.' : ''}`, 
        'success'
      );
      
      // Обновить данные
      fetchArrivedTransportCargo(selectedArrivedTransport.id);
      fetchArrivedTransports();
      
      // Закрыть модал и сбросить форму
      setQrPlacementModal(false);
      setQrPlacementForm({
        cargo_number: '',
        qr_data: '',
        cell_qr_data: '',
        block_number: 1,
        shelf_number: 1,
        cell_number: 1
      });
      
      if (response.transport_status === 'completed') {
        showAlert('Все грузы размещены! Транспорт завершен.', 'info');
        setArrivedTransportModal(false);
      }
    } catch (error) {
      console.error('Error placing cargo by QR/number:', error);
      showAlert('Ошибка размещения груза по номеру/QR', 'error');
    }
  };

  // Operator Functions
  const fetchOperatorWarehouses = async () => {
    try {
      const data = await apiCall('/api/operator/my-warehouses');
      setOperatorWarehouses(data.warehouses || []);
    } catch (error) {
      console.error('Error fetching operator warehouses:', error);
    }
  };

  const fetchTransportsList = async () => {
    try {
      const data = await apiCall('/api/transport/list');
      setTransports(data);
    } catch (error) {
      console.error('Error fetching transports list:', error);
    }
  };

  const handleCreateInterwarehouseTransport = async (e) => {
    e.preventDefault();
    try {
      const response = await apiCall('/api/transport/create-interwarehouse', 'POST', interwarehouseForm);
      
      showAlert(
        `Межскладской транспорт ${response.transport_number} создан успешно! Направление: ${response.direction}`, 
        'success'
      );
      
      // Обновить данные и закрыть модал
      fetchTransportsList();
      setInterwarehouseTransportModal(false);
      setInterwarehouseForm({
        source_warehouse_id: '',
        destination_warehouse_id: '',
        driver_name: '',
        driver_phone: '',
        capacity_kg: 1000
      });
    } catch (error) {
      console.error('Error creating interwarehouse transport:', error);
      showAlert('Ошибка создания межскладского транспорта', 'error');
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
        cargo_name: '',
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
        
        <div class="section">
          <div class="section-title">Обработка груза</div>
          ${cargo.created_by_operator ? `
          <div class="info-row">
            <span class="info-label">Принял оператор:</span>
            <span>${cargo.created_by_operator}</span>
          </div>
          ` : ''}
          ${cargo.placed_by_operator ? `
          <div class="info-row">
            <span class="info-label">Разместил оператор:</span>
            <span>${cargo.placed_by_operator}</span>
          </div>
          ` : ''}
          <div class="info-row">
            <span class="info-label">Текущий статус:</span>
            <span>${cargo.status === 'created' ? 'Создан' : 
                   cargo.status === 'accepted' ? 'Принят' : 
                   cargo.status === 'in_transit' ? 'В пути' : 
                   cargo.status === 'arrived_destination' ? 'Прибыл в пункт назначения' : 
                   cargo.status === 'completed' ? 'Доставлен' : cargo.status}</span>
          </div>
        </div>
        
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
    setContactModal(false);
    // Clear operator-warehouse binding states
    setOperatorWarehouseBindings([]);
    setOperatorBindingModal(false);
    setSelectedOperatorForBinding('');
    setSelectedWarehouseForBinding('');
    // Clear warehouse cell management states
    setSelectedCellCargo(null);
    setCargoDetailModal(false);
    setCargoEditModal(false);
    setCargoMoveModal(false);
    setEditingCargo(null);
    setCargoEditForm({});
    setCargoMoveForm({
      warehouse_id: '',
      block_number: '',
      shelf_number: '',
      cell_number: ''
    });
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
          { id: 'users-admins', label: 'Администраторы' },
          { id: 'users-operator-bindings', label: 'Привязка операторов' }
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

          {/* Кнопка связаться с нами в конце меню */}
          <div className="mt-8 pt-4 border-t border-gray-700">
            <button
              onClick={() => setContactModal(true)}
              className="w-full flex items-center px-3 py-2 rounded-lg transition-colors text-gray-300 hover:bg-gray-800 hover:text-white"
            >
              <MessageCircle className="w-5 h-5" />
              {sidebarOpen && <span className="ml-3">Связаться с нами</span>}
            </button>
          </div>
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
                      {/* Роль убрана - всегда USER по умолчанию (Функция 3) */}
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
              <TabsList className="grid w-full grid-cols-4">
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
                <TabsTrigger value="contact" className="flex items-center">
                  <MessageCircle className="mr-2 h-4 w-4" />
                  Связаться
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
                                <p><strong>Название груза:</strong> {request.cargo_name}</p>
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
                                  <p className="text-sm text-gray-600">{item.cargo_name}</p>
                                  <p className="text-xs text-gray-500">Получатель: {item.recipient_name}</p>
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

              {/* Связаться с нами */}
              <TabsContent value="contact">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <MessageCircle className="mr-2 h-5 w-5" />
                      Связаться с нами
                    </CardTitle>
                    <CardDescription>
                      Выберите удобный способ связи с нашей службой поддержки
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* WhatsApp */}
                      <Card className="p-4 hover:bg-green-50 cursor-pointer transition-colors" onClick={handleWhatsAppContact}>
                        <div className="text-center space-y-3">
                          <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto">
                            <MessageCircle className="w-8 h-8 text-white" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-green-700">WhatsApp</h3>
                            <p className="text-sm text-gray-600">Быстрая связь через мессенджер</p>
                            <p className="text-xs text-gray-500 mt-1">+7 (912) 345-67-89</p>
                          </div>
                          <Button className="w-full bg-green-500 hover:bg-green-600">
                            Написать в WhatsApp
                          </Button>
                        </div>
                      </Card>

                      {/* Telegram */}
                      <Card className="p-4 hover:bg-blue-50 cursor-pointer transition-colors" onClick={handleTelegramContact}>
                        <div className="text-center space-y-3">
                          <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mx-auto">
                            <MessageCircle className="w-8 h-8 text-white" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-blue-700">Telegram</h3>
                            <p className="text-sm text-gray-600">Общение в мессенджере</p>
                            <p className="text-xs text-gray-500 mt-1">@tajline_support</p>
                          </div>
                          <Button className="w-full bg-blue-500 hover:bg-blue-600">
                            Написать в Telegram
                          </Button>
                        </div>
                      </Card>

                      {/* Онлайн чат */}
                      <Card className="p-4 hover:bg-purple-50 cursor-pointer transition-colors" onClick={handleOnlineChat}>
                        <div className="text-center space-y-3">
                          <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center mx-auto">
                            <MessageCircle className="w-8 h-8 text-white" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-purple-700">Онлайн чат</h3>
                            <p className="text-sm text-gray-600">Прямая связь с оператором</p>
                            <p className="text-xs text-gray-500 mt-1">Мгновенные ответы</p>
                          </div>
                          <Button className="w-full bg-purple-500 hover:bg-purple-600">
                            Начать чат
                          </Button>
                        </div>
                      </Card>
                    </div>

                    {/* Информация о времени работы */}
                    <div className="mt-6 bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-center space-x-2 mb-3">
                        <Clock className="w-5 h-5 text-gray-500" />
                        <span className="font-medium text-gray-700">Время работы поддержки</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                        <div>
                          <p><strong>Понедельник - Пятница:</strong></p>
                          <p>9:00 - 18:00 (МСК)</p>
                        </div>
                        <div>
                          <p><strong>Суббота - Воскресенье:</strong></p>
                          <p>10:00 - 16:00 (МСК)</p>
                        </div>
                      </div>
                      <div className="mt-3 p-2 bg-green-100 rounded text-sm text-green-700">
                        💬 WhatsApp и Telegram доступны 24/7
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            /* Для админа и оператора склада - новый интерфейс с боковым меню */
            <div className="space-y-6">
              
              {/* Шапка с поиском и уведомлениями */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    
                    {/* Поиск */}
                    <div className="flex-1 max-w-md relative">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          placeholder="Поиск по номеру, ФИО, телефону..."
                          value={searchQuery}
                          onChange={(e) => {
                            setSearchQuery(e.target.value);
                            if (e.target.value.length >= 2) {
                              handleSearch(e.target.value);
                            } else {
                              clearSearch();
                            }
                          }}
                          className="pl-10 pr-8"
                        />
                        {searchQuery && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                            onClick={clearSearch}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                      
                      {/* Результаты поиска */}
                      {showSearchResults && (
                        <div className="absolute z-50 mt-2 w-full bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto"
                        >
                          {searchResults.length === 0 ? (
                            <div className="p-4 text-gray-500 text-center">Ничего не найдено</div>
                          ) : (
                            searchResults.map((result) => (
                              <div
                                key={result.id}
                                className="p-3 border-b hover:bg-gray-50 cursor-pointer"
                                onClick={async () => {
                                  try {
                                    const cargoDetails = await fetchCargoDetails(result.id);
                                    setSelectedCellCargo(cargoDetails);
                                    setCargoDetailModal(true);
                                    clearSearch();
                                  } catch (error) {
                                    console.error('Error fetching cargo details:', error);
                                  }
                                }}
                              >
                                <div className="font-medium">{result.cargo_number}</div>
                                <div className="text-sm text-gray-600">{result.cargo_name}</div>
                                <div className="text-xs text-gray-500">
                                  {result.sender_full_name} → {result.recipient_full_name || result.recipient_name}
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      )}
                    </div>
                    
                    {/* Фильтр поиска */}
                    <Select value={searchType} onValueChange={setSearchType}>
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Везде</SelectItem>
                        <SelectItem value="number">По номеру</SelectItem>
                        <SelectItem value="sender_name">По отправителю</SelectItem>
                        <SelectItem value="recipient_name">По получателю</SelectItem>
                        <SelectItem value="phone">По телефону</SelectItem>
                        <SelectItem value="cargo_name">По названию</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    {/* Статистика и быстрый доступ */}
                    <div className="flex items-center space-x-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setQrScannerModal(true)}
                        title="Сканировать QR код"
                      >
                        <Camera className="h-4 w-4 mr-2" />
                        QR сканер
                      </Button>
                      
                      <div className="text-sm text-gray-600">
                        Всего грузов: <span className="font-medium">{cargo.length}</span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          fetchNotifications();
                          fetchSystemNotifications();
                        }}
                      >
                        <Bell className="h-4 w-4 mr-2" />
                        Обновить
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

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

                          <div>
                            <Label htmlFor="cargo_name">Название груза</Label>
                            <Input
                              id="cargo_name"
                              value={operatorCargoForm.cargo_name}
                              onChange={(e) => setOperatorCargoForm({...operatorCargoForm, cargo_name: e.target.value})}
                              placeholder="Документы, личные вещи, электроника"
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
                                        <p><strong>Название:</strong> {item.cargo_name}</p>
                                        <p><strong>От:</strong> {item.sender_full_name} ({item.sender_phone})</p>
                                        <p><strong>Для:</strong> {item.recipient_full_name} ({item.recipient_phone})</p>
                                        <p><strong>Вес:</strong> {item.weight} кг</p>
                                        <p><strong>Описание:</strong> {item.description}</p>
                                        {item.created_by_operator && (
                                          <p><strong>Принял:</strong> {item.created_by_operator}</p>
                                        )}
                                        {item.placed_by_operator && (
                                          <p><strong>Разместил:</strong> {item.placed_by_operator}</p>
                                        )}
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

                  {/* Привязка операторов к складам */}
                  {activeTab === 'users-operator-bindings' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Users className="mr-2 h-5 w-5" />
                            Привязка операторов к складам ({operatorWarehouseBindings.length})
                          </div>
                          <Button onClick={() => setOperatorBindingModal(true)}>
                            <Plus className="mr-2 h-4 w-4" />
                            Создать привязку
                          </Button>
                        </CardTitle>
                        <CardDescription>
                          Управление доступом операторов к складам
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        {operatorWarehouseBindings.length === 0 ? (
                          <div className="text-center py-8">
                            <Users className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                            <p className="text-gray-500">Нет привязок операторов к складам</p>
                            <Button 
                              onClick={() => setOperatorBindingModal(true)}
                              className="mt-4"
                            >
                              Создать первую привязку
                            </Button>
                          </div>
                        ) : (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Оператор</TableHead>
                                <TableHead>Телефон</TableHead>
                                <TableHead>Склад</TableHead>
                                <TableHead>Дата создания</TableHead>
                                <TableHead>Действия</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {operatorWarehouseBindings.map((binding) => (
                                <TableRow key={binding.id}>
                                  <TableCell className="font-medium">{binding.operator_name}</TableCell>
                                  <TableCell>{binding.operator_phone}</TableCell>
                                  <TableCell>{binding.warehouse_name}</TableCell>
                                  <TableCell>
                                    {new Date(binding.created_at).toLocaleDateString('ru-RU')}
                                  </TableCell>
                                  <TableCell>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleDeleteOperatorBinding(binding.id)}
                                      className="text-red-600 hover:text-red-700"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                      Удалить
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
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
                                    
                                    <Button 
                                      size="sm" 
                                      variant="outline"
                                      onClick={() => printWarehouseCellsQr(warehouse)}
                                      title="Печать QR кодов всех ячеек"
                                    >
                                      <QrCode className="mr-2 h-4 w-4" />
                                      QR ячеек
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
                                  {item.accepted_by_operator && (
                                    <p className="text-sm text-gray-500">Принял: {item.accepted_by_operator}</p>
                                  )}
                                  {item.placed_by_operator && (
                                    <p className="text-sm text-gray-500">Разместил: {item.placed_by_operator}</p>
                                  )}
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
                          <div className="flex space-x-2">
                            <Button 
                              variant="outline" 
                              onClick={() => setInterwarehouseTransportModal(true)}
                              disabled={user?.role !== 'admin' && user?.role !== 'warehouse_operator'}
                            >
                              <Plus className="mr-2 h-4 w-4" />
                              Межскладской
                            </Button>
                            <Button onClick={() => fetchTransportsList()}>
                              Обновить
                            </Button>
                          </div>
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
                                  
                                  <div className="flex space-x-2">
                                    <Button 
                                      onClick={() => {
                                        setSelectedTransport(transport);
                                        fetchTransportCargoList(transport.id);
                                        fetchAvailableCargoForTransport();
                                        setTransportManagementModal(true);
                                      }}
                                      className="flex-1"
                                      variant="outline"
                                    >
                                      <Truck className="mr-1 h-3 w-3" />
                                      Управление
                                    </Button>
                                    
                                    <Button 
                                      onClick={() => openTransportVisualization(transport)}
                                      variant="outline"
                                      size="sm"
                                      title="Схема загрузки транспорта"
                                    >
                                      <Grid3X3 className="h-3 w-3" />
                                    </Button>
                                  </div>
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
                                  <div className="space-y-2 flex-1">
                                    <h3 className="font-semibold text-lg">{transport.transport_number}</h3>
                                    <p className="text-sm text-gray-600"><strong>Водитель:</strong> {transport.driver_name}</p>
                                    <p className="text-sm text-gray-600"><strong>Направление:</strong> {transport.direction}</p>
                                    <p className="text-sm text-gray-600"><strong>Груз:</strong> {transport.current_load_kg} кг ({transport.cargo_list.length} мест)</p>
                                    <p className="text-sm text-gray-600"><strong>Отправлен:</strong> {new Date(transport.dispatched_at).toLocaleDateString('ru-RU')} {new Date(transport.dispatched_at).toLocaleTimeString('ru-RU')}</p>
                                  </div>
                                  <div className="flex flex-col items-end space-y-2">
                                    <Badge className="bg-yellow-100 text-yellow-800">В пути</Badge>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleMarkTransportArrived(transport.id)}
                                      className="text-green-600 hover:text-green-700"
                                    >
                                      <MapPin className="mr-1 h-3 w-3" />
                                      Прибыл
                                    </Button>
                                  </div>
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
                          Прибывшие транспорты для размещения ({arrivedTransports.length})
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {arrivedTransports.length === 0 ? (
                            <div className="text-center py-8">
                              <MapPin className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Нет прибывших транспортов для размещения</p>
                            </div>
                          ) : (
                            arrivedTransports.map((transport) => (
                              <Card key={transport.id} className="p-4 border-green-200">
                                <div className="flex justify-between items-start">
                                  <div className="space-y-2 flex-1">
                                    <h3 className="font-semibold text-lg text-green-800">{transport.transport_number}</h3>
                                    <p className="text-sm text-gray-600"><strong>Водитель:</strong> {transport.driver_name}</p>
                                    <p className="text-sm text-gray-600"><strong>Направление:</strong> {transport.direction}</p>
                                    <p className="text-sm text-gray-600"><strong>Груз:</strong> {transport.current_load_kg} кг ({transport.cargo_count} мест)</p>
                                    <p className="text-sm text-gray-600"><strong>Прибыл:</strong> {new Date(transport.arrived_at).toLocaleDateString('ru-RU')} {new Date(transport.arrived_at).toLocaleTimeString('ru-RU')}</p>
                                  </div>
                                  <div className="flex flex-col items-end space-y-2">
                                    <Badge className="bg-green-100 text-green-800">Прибыл</Badge>
                                    <Button
                                      size="sm"
                                      onClick={() => {
                                        setSelectedArrivedTransport(transport);
                                        fetchArrivedTransportCargo(transport.id);
                                        setArrivedTransportModal(true);
                                      }}
                                      className="bg-blue-600 hover:bg-blue-700 text-white"
                                    >
                                      <Package className="mr-1 h-3 w-3" />
                                      Разместить грузы
                                    </Button>
                                  </div>
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
                                  className={`p-2 text-xs text-center rounded border-2 transition-all cursor-pointer hover:scale-105 ${
                                    cell.is_occupied 
                                      ? 'bg-red-100 border-red-300 text-red-800 hover:bg-red-200' 
                                      : 'bg-green-100 border-green-300 text-green-800 hover:bg-green-200'
                                  }`}
                                  title={cell.cargo_info ? `${cell.cargo_info.cargo_number} - ${cell.cargo_info.sender_name}` : 'Свободная ячейка'}
                                  onClick={() => {
                                    if (cell.is_occupied && cell.cargo_info) {
                                      const locationCode = `B${block.block_number}-S${shelf.shelf_number}-C${cell.cell_number}`;
                                      handleCellClick(selectedWarehouseForLayout.id, locationCode);
                                    } else {
                                      showAlert('Ячейка свободна', 'info');
                                    }
                                  }}
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
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Управление транспортом {selectedTransport?.transport_number}
            </DialogTitle>
            <DialogDescription>
              Полная информация и управление транспортом
            </DialogDescription>
          </DialogHeader>
          
          {selectedTransport && (
            <div className="space-y-6">
              {/* Информация о транспорте */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">Информация о транспорте</h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <p><strong>Номер:</strong> {selectedTransport.transport_number}</p>
                  <p><strong>Водитель:</strong> {selectedTransport.driver_name}</p>
                  <p><strong>Телефон:</strong> {selectedTransport.driver_phone}</p>
                  <p><strong>Направление:</strong> {selectedTransport.direction}</p>
                  <p><strong>Вместимость:</strong> {selectedTransport.capacity_kg} кг</p>
                  <p><strong>Текущая загрузка:</strong> {selectedTransport.current_load_kg} кг</p>
                  <p><strong>Процент загрузки:</strong> {Math.round((selectedTransport.current_load_kg / selectedTransport.capacity_kg) * 100)}%</p>
                  <p><strong>Статус:</strong> 
                    <Badge className="ml-2" variant={selectedTransport.status === 'empty' ? 'secondary' : 'default'}>
                      {selectedTransport.status === 'empty' ? 'Пустой' : selectedTransport.status === 'filled' ? 'Заполнено' : selectedTransport.status}
                    </Badge>
                  </p>
                  <p><strong>Количество грузов:</strong> {transportCargoList.cargo_count || 0} мест</p>
                </div>
              </div>

              {/* Список размещенных грузов */}
              <Card className="p-4">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-semibold">Грузы на транспорте ({transportCargoList.cargo_count || 0} мест)</h4>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (transportCargoList.cargo_list && transportCargoList.cargo_list.length > 0) {
                          printTransportCargoList(selectedTransport, transportCargoList.cargo_list);
                        }
                      }}
                    >
                      <Printer className="h-4 w-4 mr-2" />
                      Печать списка
                    </Button>
                  </div>
                </div>
                
                <div className="max-h-60 overflow-y-auto border rounded">
                  {!transportCargoList.cargo_list || transportCargoList.cargo_list.length === 0 ? (
                    <p className="p-4 text-gray-500 text-center">Груз не размещен</p>
                  ) : (
                    <div className="space-y-2 p-2">
                      {transportCargoList.cargo_list.map((cargo, index) => (
                        <div key={cargo.id} className="flex justify-between items-center p-3 bg-gray-50 rounded border">
                          <div className="flex-1">
                            <div className="flex items-center space-x-4">
                              <div>
                                <p className="font-medium">{cargo.cargo_number}</p>
                                <p className="text-sm text-gray-600">{cargo.cargo_name || 'Груз'}</p>
                              </div>
                              <div>
                                <p className="text-sm"><strong>Вес:</strong> {cargo.weight} кг</p>
                                <p className="text-sm"><strong>Получатель:</strong> {cargo.recipient_name}</p>
                              </div>
                            </div>
                            <div className="mt-2 text-xs text-gray-500">
                              <p><strong>Отправитель:</strong> {cargo.sender_full_name || 'Не указан'} - {cargo.sender_phone || 'Нет телефона'}</p>
                              <p><strong>Получатель:</strong> {cargo.recipient_full_name || cargo.recipient_name} - {cargo.recipient_phone || 'Нет телефона'}</p>
                              {cargo.recipient_address && (
                                <p><strong>Адрес:</strong> {cargo.recipient_address}</p>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex space-x-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                try {
                                  const fullCargoDetails = await fetchCargoDetails(cargo.id);
                                  setSelectedCellCargo(fullCargoDetails);
                                  setCargoDetailModal(true);
                                } catch (error) {
                                  console.error('Error fetching cargo details:', error);
                                }
                              }}
                            >
                              <User className="h-4 w-4" />
                            </Button>
                            
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => printCargoQrLabel(cargo)}
                              title="Печать QR этикетки"
                            >
                              <QrCode className="h-4 w-4" />
                            </Button>
                            
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                if (window.confirm(`Вернуть груз ${cargo.cargo_number} в исходное место на складе?`)) {
                                  try {
                                    // Return cargo to its original warehouse location
                                    await apiCall(`/api/transport/${selectedTransport.id}/remove-cargo/${cargo.id}`, 'DELETE');
                                    showAlert(`Груз ${cargo.cargo_number} возвращен на склад!`, 'success');
                                    fetchTransportCargoList(selectedTransport.id);
                                    fetchTransports();
                                  } catch (error) {
                                    console.error('Error returning cargo:', error);
                                    showAlert('Ошибка при возврате груза на склад', 'error');
                                  }
                                }
                              }}
                              className="text-orange-600 hover:text-orange-700"
                            >
                              <Package className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {transportCargoList.cargo_list && transportCargoList.cargo_list.length > 0 && (
                  <div className="mt-4 p-3 bg-blue-50 rounded">
                    <p className="text-sm"><strong>Общий вес:</strong> {transportCargoList.total_weight || 0} кг</p>
                    <p className="text-sm"><strong>Остаток вместимости:</strong> {selectedTransport.capacity_kg - (transportCargoList.total_weight || 0)} кг</p>
                  </div>
                )}
              </Card>

              {/* Размещение нового груза */}
              <Card className="p-4">
                <h4 className="font-semibold mb-3">Размещение нового груза</h4>
                <p className="text-sm text-gray-600 mb-4">
                  Введите номера грузов для размещения на транспорт
                </p>
                
                <div className="mb-4">
                  <Label htmlFor="cargo-numbers">Номера грузов (через запятую):</Label>
                  <Input
                    id="cargo-numbers"
                    placeholder="Например: 1001, 1002, 1003"
                    value={selectedCargoForPlacement.join(', ')}
                    onChange={(e) => {
                      const cargoNumbers = e.target.value.split(',').map(num => num.trim()).filter(num => num);
                      setSelectedCargoForPlacement(cargoNumbers);
                    }}
                    className="mt-2"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Введите номера грузов через запятую. Грузы должны находиться на складе.
                  </p>
                </div>
                
                <Button 
                  onClick={() => handlePlaceCargoOnTransport(selectedTransport.id, selectedCargoForPlacement)}
                  disabled={selectedCargoForPlacement.length === 0}
                  className="w-full"
                >
                  Разместить груз
                </Button>
              </Card>

              {/* Действия с транспортом */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Отправить транспорт */}
                <Card className="p-4">
                  <h4 className="font-semibold mb-3">Отправить транспорт</h4>
                  <p className="text-sm text-gray-600 mb-4">
                    Отправить транспорт в место назначения с любым количеством груза
                  </p>
                  <Button 
                    onClick={() => handleDispatchTransport(selectedTransport.id)}
                    disabled={selectedTransport.status === 'in_transit'}
                    className="w-full"
                  >
                    {selectedTransport.status === 'in_transit' ? 'Транспорт уже в пути' : 'Отправить транспорт'}
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

      {/* Модальное окно "Связаться с нами" */}
      <Dialog open={contactModal} onOpenChange={setContactModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <MessageCircle className="mr-2 h-5 w-5" />
              Связаться с нами
            </DialogTitle>
            <DialogDescription>
              Выберите удобный способ связи с нашей службой поддержки
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* WhatsApp */}
            <Card className="p-4 hover:bg-green-50 cursor-pointer transition-colors" onClick={handleWhatsAppContact}>
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-green-700">WhatsApp</h3>
                  <p className="text-sm text-gray-600">Быстрая связь через мессенджер</p>
                  <p className="text-xs text-gray-500">+7 (912) 345-67-89</p>
                </div>
                <div className="text-green-500">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.488"/>
                  </svg>
                </div>
              </div>
            </Card>

            {/* Telegram */}
            <Card className="p-4 hover:bg-blue-50 cursor-pointer transition-colors" onClick={handleTelegramContact}>
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-700">Telegram</h3>
                  <p className="text-sm text-gray-600">Общение в мессенджере</p>
                  <p className="text-xs text-gray-500">@tajline_support</p>
                </div>
                <div className="text-blue-500">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                  </svg>
                </div>
              </div>
            </Card>

            {/* Онлайн чат */}
            <Card className="p-4 hover:bg-purple-50 cursor-pointer transition-colors" onClick={handleOnlineChat}>
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-purple-700">Онлайн чат</h3>
                  <p className="text-sm text-gray-600">Прямая связь с оператором</p>
                  <p className="text-xs text-gray-500">Мгновенные ответы</p>
                </div>
                <div className="text-purple-500">
                  <MessageCircle className="w-5 h-5" />
                </div>
              </div>
            </Card>

            {/* Информация о времени работы */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Время работы поддержки</span>
              </div>
              <p className="text-xs text-gray-600">Понедельник - Пятница: 9:00 - 18:00 (МСК)</p>
              <p className="text-xs text-gray-600">Суббота - Воскресенье: 10:00 - 16:00 (МСК)</p>
              <p className="text-xs text-green-600 mt-1">WhatsApp и Telegram доступны 24/7</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно создания привязки оператора к складу */}
      <Dialog open={operatorBindingModal} onOpenChange={setOperatorBindingModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Привязать оператора к складу</DialogTitle>
            <DialogDescription>
              Выберите оператора и склад для создания привязки
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="operator-select">Выберите оператора</Label>
              <Select value={selectedOperatorForBinding} onValueChange={setSelectedOperatorForBinding}>
                <SelectTrigger id="operator-select">
                  <SelectValue placeholder="Выберите оператора склада" />
                </SelectTrigger>
                <SelectContent>
                  {usersByRole.warehouse_operator.map((operator) => (
                    <SelectItem key={operator.id} value={operator.id}>
                      {operator.full_name} ({operator.phone})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="warehouse-select">Выберите склад</Label>
              <Select value={selectedWarehouseForBinding} onValueChange={setSelectedWarehouseForBinding}>
                <SelectTrigger id="warehouse-select">
                  <SelectValue placeholder="Выберите склад" />
                </SelectTrigger>
                <SelectContent>
                  {warehouses.map((warehouse) => (
                    <SelectItem key={warehouse.id} value={warehouse.id}>
                      {warehouse.name} ({warehouse.location})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button
                variant="outline"
                onClick={() => {
                  setOperatorBindingModal(false);
                  setSelectedOperatorForBinding('');
                  setSelectedWarehouseForBinding('');
                }}
              >
                Отмена
              </Button>
              <Button onClick={handleCreateOperatorBinding}>
                Создать привязку
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно детального просмотра груза */}
      <Dialog open={cargoDetailModal} onOpenChange={setCargoDetailModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Детальная информация о грузе {selectedCellCargo?.cargo_number}
            </DialogTitle>
          </DialogHeader>
          
          {selectedCellCargo && (
            <div className="space-y-4">
              {/* Основная информация */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p><strong>Номер груза:</strong> {selectedCellCargo.cargo_number}</p>
                  <p><strong>Название:</strong> {selectedCellCargo.cargo_name || 'Не указано'}</p>
                  <p><strong>Вес:</strong> {selectedCellCargo.weight} кг</p>
                  <p><strong>Стоимость:</strong> {selectedCellCargo.declared_value} руб.</p>
                </div>
                <div>
                  <p><strong>Дата приёма:</strong> {new Date(selectedCellCargo.created_at).toLocaleDateString('ru-RU')}</p>
                  <p><strong>Статус:</strong> {selectedCellCargo.status}</p>
                  <p><strong>Статус оплаты:</strong> {selectedCellCargo.payment_status || 'pending'}</p>
                  {selectedCellCargo.warehouse_location && (
                    <p><strong>Местоположение:</strong> {selectedCellCargo.warehouse_location}</p>
                  )}
                </div>
              </div>

              {/* Информация об отправителе */}
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Отправитель</h3>
                <p><strong>ФИО:</strong> {selectedCellCargo.sender_full_name}</p>
                <p><strong>Телефон:</strong> {selectedCellCargo.sender_phone}</p>
              </div>

              {/* Информация о получателе */}
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Получатель</h3>
                <p><strong>ФИО:</strong> {selectedCellCargo.recipient_full_name || selectedCellCargo.recipient_name}</p>
                <p><strong>Телефон:</strong> {selectedCellCargo.recipient_phone}</p>
                <p><strong>Адрес:</strong> {selectedCellCargo.recipient_address}</p>
              </div>

              {/* Информация об операторах */}
              <div className="p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold mb-2">Обработка</h3>
                {selectedCellCargo.created_by_operator && (
                  <p><strong>Принял оператор:</strong> {selectedCellCargo.created_by_operator}</p>
                )}
                {selectedCellCargo.placed_by_operator && (
                  <p><strong>Разместил оператор:</strong> {selectedCellCargo.placed_by_operator}</p>
                )}
              </div>

              {/* Кнопки действий */}
              <div className="flex flex-wrap gap-2 pt-4">
                <Button onClick={() => handleEditCargo(selectedCellCargo)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Редактировать
                </Button>
                
                {selectedCellCargo.warehouse_location && (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => handleMoveCargo(selectedCellCargo)}
                    >
                      <Package className="mr-2 h-4 w-4" />
                      Переместить
                    </Button>
                    
                    <Button
                      variant="destructive"
                      onClick={() => handleRemoveCargoFromCell(selectedCellCargo)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Удалить из ячейки
                    </Button>
                  </>
                )}
                
                <div className="flex space-x-2">
                  <Button variant="outline" onClick={() => printInvoice(selectedCellCargo)}>
                    <Printer className="mr-2 h-4 w-4" />
                    Печать накладной
                  </Button>
                  
                  <Button variant="outline" onClick={() => printCargoQrLabel(selectedCellCargo)}>
                    <QrCode className="mr-2 h-4 w-4" />
                    QR этикетка
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Модальное окно редактирования груза */}
      <Dialog open={cargoEditModal} onOpenChange={setCargoEditModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Редактирование груза {editingCargo?.cargo_number}</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_cargo_name">Название груза</Label>
                <Input
                  id="edit_cargo_name"
                  value={cargoEditForm.cargo_name || ''}
                  onChange={(e) => setCargoEditForm({...cargoEditForm, cargo_name: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit_weight">Вес (кг)</Label>
                <Input
                  id="edit_weight"
                  type="number"
                  step="0.1"
                  value={cargoEditForm.weight || ''}
                  onChange={(e) => setCargoEditForm({...cargoEditForm, weight: parseFloat(e.target.value)})}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="edit_description">Описание</Label>
              <Textarea
                id="edit_description"
                value={cargoEditForm.description || ''}
                onChange={(e) => setCargoEditForm({...cargoEditForm, description: e.target.value})}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_sender_name">ФИО отправителя</Label>
                <Input
                  id="edit_sender_name"
                  value={cargoEditForm.sender_full_name || ''}
                  onChange={(e) => setCargoEditForm({...cargoEditForm, sender_full_name: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit_sender_phone">Телефон отправителя</Label>
                <Input
                  id="edit_sender_phone"
                  value={cargoEditForm.sender_phone || ''}
                  onChange={(e) => setCargoEditForm({...cargoEditForm, sender_phone: e.target.value})}
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setCargoEditModal(false)}>
                Отмена
              </Button>
              <Button onClick={handleUpdateCargo}>
                Сохранить изменения
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно перемещения груза */}
      <Dialog open={cargoMoveModal} onOpenChange={setCargoMoveModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Перемещение груза {editingCargo?.cargo_number}</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="move_warehouse">Склад</Label>
              <Select
                value={cargoMoveForm.warehouse_id}
                onValueChange={(value) => setCargoMoveForm({...cargoMoveForm, warehouse_id: value})}
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

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="move_block">Блок</Label>
                <Input
                  id="move_block"
                  type="number"
                  min="1"
                  value={cargoMoveForm.block_number}
                  onChange={(e) => setCargoMoveForm({...cargoMoveForm, block_number: parseInt(e.target.value)})}
                />
              </div>
              <div>
                <Label htmlFor="move_shelf">Полка</Label>
                <Input
                  id="move_shelf"
                  type="number"
                  min="1"
                  value={cargoMoveForm.shelf_number}
                  onChange={(e) => setCargoMoveForm({...cargoMoveForm, shelf_number: parseInt(e.target.value)})}
                />
              </div>
              <div>
                <Label htmlFor="move_cell">Ячейка</Label>
                <Input
                  id="move_cell"
                  type="number"
                  min="1"
                  value={cargoMoveForm.cell_number}
                  onChange={(e) => setCargoMoveForm({...cargoMoveForm, cell_number: parseInt(e.target.value)})}
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button variant="outline" onClick={() => setCargoMoveModal(false)}>
                Отмена
              </Button>
              <Button onClick={handleMoveCargoSubmit}>
                Переместить
              </Button>
            </div>
          </div>
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

      {/* QR Scanner Modal */}
      <Dialog open={qrScannerModal} onOpenChange={setQrScannerModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              <Camera className="mr-2 h-5 w-5 inline" />
              Сканировать QR код
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="text-center">
              <div className="w-64 h-64 bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center mx-auto mb-4">
                <div className="text-center">
                  <Camera className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">QR сканер</p>
                  <p className="text-xs text-gray-400 mt-1">Наведите камеру на QR код</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-4">
                Отсканируйте QR код груза или ячейки склада для быстрого доступа к информации
              </p>
              
              {/* Manual input for testing */}
              <div className="text-left">
                <Label htmlFor="manual-qr">Или введите данные QR кода вручную:</Label>
                <textarea
                  id="manual-qr"
                  className="w-full mt-2 p-3 border rounded-md"
                  rows="4"
                  placeholder="Вставьте содержимое QR кода здесь..."
                  onChange={(e) => {
                    if (e.target.value.trim()) {
                      handleQrScan(e.target.value.trim());
                      e.target.value = '';
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* QR Scan Result Modal */}
      {qrScanResult && (
        <Dialog open={!!qrScanResult} onOpenChange={() => setQrScanResult(null)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                <QrCode className="mr-2 h-5 w-5 inline" />
                Результат сканирования
              </DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              {qrScanResult.type === 'cargo' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div>
                      <h3 className="font-semibold text-blue-800">Груз найден!</h3>
                      <p className="text-sm text-blue-600">№{qrScanResult.cargo_number}</p>
                    </div>
                    <Package className="h-8 w-8 text-blue-600" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Наименование:</span>
                      <span className="text-sm">{qrScanResult.cargo_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Вес:</span>
                      <span className="text-sm">{qrScanResult.weight} кг</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Статус:</span>
                      <Badge variant="outline">{qrScanResult.status}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Отправитель:</span>
                      <span className="text-sm">{qrScanResult.sender}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Получатель:</span>
                      <span className="text-sm">{qrScanResult.recipient}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Местоположение:</span>
                      <span className="text-sm">{qrScanResult.location}</span>
                    </div>
                  </div>
                  
                  <Button 
                    className="w-full" 
                    onClick={async () => {
                      try {
                        const cargoDetails = await fetchCargoDetails(qrScanResult.cargo_id);
                        setSelectedCellCargo(cargoDetails);
                        setCargoDetailModal(true);
                        setQrScanResult(null);
                      } catch (error) {
                        console.error('Error fetching cargo details:', error);
                      }
                    }}
                  >
                    Подробная информация
                  </Button>
                </div>
              )}
              
              {qrScanResult.type === 'warehouse_cell' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div>
                      <h3 className="font-semibold text-green-800">Ячейка склада</h3>
                      <p className="text-sm text-green-600">{qrScanResult.location}</p>
                    </div>
                    <Building className="h-8 w-8 text-green-600" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Склад:</span>
                      <span className="text-sm">{qrScanResult.warehouse_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Блок:</span>
                      <span className="text-sm">{qrScanResult.block}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Полка:</span>
                      <span className="text-sm">{qrScanResult.shelf}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Ячейка:</span>
                      <span className="text-sm">{qrScanResult.cell}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">Статус:</span>
                      <Badge variant={qrScanResult.is_occupied ? "destructive" : "default"}>
                        {qrScanResult.is_occupied ? "Занята" : "Свободна"}
                      </Badge>
                    </div>
                    
                    {qrScanResult.cargo && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                        <h4 className="font-medium text-sm mb-2">Груз в ячейке:</h4>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-xs">Номер:</span>
                            <span className="text-xs font-medium">{qrScanResult.cargo.cargo_number}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-xs">Название:</span>
                            <span className="text-xs">{qrScanResult.cargo.cargo_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-xs">Вес:</span>
                            <span className="text-xs">{qrScanResult.cargo.weight} кг</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <Button 
                    className="w-full" 
                    variant="outline"
                    onClick={() => {
                      // Navigate to warehouse management
                      const warehouse = warehouses.find(w => w.id === qrScanResult.warehouse_id);
                      if (warehouse) {
                        handleOpenWarehouseLayout(warehouse);
                        setQrScanResult(null);
                      }
                    }}
                  >
                    Перейти к управлению складом
                  </Button>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Arrived Transport Modal */}
      <Dialog open={arrivedTransportModal} onOpenChange={setArrivedTransportModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              <Truck className="mr-2 h-5 w-5 inline" />
              Размещение грузов из транспорта {selectedArrivedTransport?.transport_number}
            </DialogTitle>
          </DialogHeader>
          
          {selectedArrivedTransport && (
            <div className="space-y-6">
              {/* Информация о транспорте */}
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-semibold text-green-800 mb-2">Информация о транспорте</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <p><strong>Номер:</strong> {selectedArrivedTransport.transport_number}</p>
                  <p><strong>Водитель:</strong> {selectedArrivedTransport.driver_name}</p>
                  <p><strong>Направление:</strong> {selectedArrivedTransport.direction}</p>
                  <p><strong>Прибыл:</strong> {new Date(selectedArrivedTransport.arrived_at).toLocaleString('ru-RU')}</p>
                </div>
              </div>

              {/* Список грузов для размещения */}
              <Card className="p-4">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-semibold">Грузы для размещения ({arrivedCargoList.placeable_cargo_count || 0} из {arrivedCargoList.cargo_count || 0})</h4>
                  <div className="flex items-center space-x-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setQrPlacementModal(true)}
                      className="text-purple-600 hover:text-purple-700"
                    >
                      <QrCode className="h-4 w-4 mr-1" />
                      QR Размещение
                    </Button>
                    <div className="text-sm text-gray-600">
                      Общий вес: {arrivedCargoList.total_weight || 0} кг
                    </div>
                  </div>
                </div>
                
                <div className="max-h-80 overflow-y-auto border rounded">
                  {!arrivedCargoList.cargo_list || arrivedCargoList.cargo_list.length === 0 ? (
                    <p className="p-4 text-gray-500 text-center">Нет грузов для размещения</p>
                  ) : (
                    <div className="space-y-2 p-2">
                      {arrivedCargoList.cargo_list.map((cargo) => (
                        <div key={cargo.id} className={`flex justify-between items-center p-3 rounded border ${cargo.can_be_placed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                          <div className="flex-1">
                            <div className="flex items-center space-x-4">
                              <div>
                                <p className="font-medium">{cargo.cargo_number}</p>
                                <p className="text-sm text-gray-600">{cargo.cargo_name}</p>
                              </div>
                              <div>
                                <p className="text-sm"><strong>Вес:</strong> {cargo.weight} кг</p>
                                <p className="text-sm"><strong>Получатель:</strong> {cargo.recipient_full_name}</p>
                              </div>
                              <div>
                                <Badge variant={cargo.can_be_placed ? "default" : "secondary"}>
                                  {cargo.status === 'arrived_destination' ? 'Готов к размещению' : cargo.status}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex space-x-2">
                            {cargo.can_be_placed && (
                              <Button
                                size="sm"
                                onClick={() => {
                                  setSelectedCargoForWarehouse(cargo);
                                  setCargoPlacementModal(true);
                                }}
                                className="bg-blue-600 hover:bg-blue-700 text-white"
                              >
                                <Building className="h-4 w-4 mr-1" />
                                Разместить
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Cargo Placement Modal */}
      <Dialog open={cargoPlacementModal} onOpenChange={setCargoPlacementModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              <Building className="mr-2 h-5 w-5 inline" />
              Размещение груза {selectedCargoForWarehouse?.cargo_number}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handlePlaceCargoFromTransport} className="space-y-4">
            {selectedCargoForWarehouse && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <h5 className="font-medium text-blue-800">Информация о грузе</h5>
                <p className="text-sm"><strong>Номер:</strong> {selectedCargoForWarehouse.cargo_number}</p>
                <p className="text-sm"><strong>Название:</strong> {selectedCargoForWarehouse.cargo_name}</p>
                <p className="text-sm"><strong>Вес:</strong> {selectedCargoForWarehouse.weight} кг</p>
                <p className="text-sm"><strong>Получатель:</strong> {selectedCargoForWarehouse.recipient_full_name}</p>
              </div>
            )}

            <div>
              <Label htmlFor="placement_warehouse">Склад</Label>
              <Select 
                value={placementForm.warehouse_id} 
                onValueChange={(value) => setPlacementForm({...placementForm, warehouse_id: value})}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите склад" />
                </SelectTrigger>
                <SelectContent>
                  {warehouses.map((warehouse) => (
                    <SelectItem key={warehouse.id} value={warehouse.id}>
                      {warehouse.name} ({warehouse.location})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label htmlFor="placement_block">Блок</Label>
                <Select 
                  value={placementForm.block_number.toString()} 
                  onValueChange={(value) => setPlacementForm({...placementForm, block_number: parseInt(value)})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {placementForm.warehouse_id && warehouses.find(w => w.id === placementForm.warehouse_id) && 
                      Array.from({length: warehouses.find(w => w.id === placementForm.warehouse_id).blocks_count}, (_, i) => (
                        <SelectItem key={i+1} value={(i+1).toString()}>{i+1}</SelectItem>
                      ))
                    }
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="placement_shelf">Полка</Label>
                <Select 
                  value={placementForm.shelf_number.toString()} 
                  onValueChange={(value) => setPlacementForm({...placementForm, shelf_number: parseInt(value)})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {placementForm.warehouse_id && warehouses.find(w => w.id === placementForm.warehouse_id) && 
                      Array.from({length: warehouses.find(w => w.id === placementForm.warehouse_id).shelves_per_block}, (_, i) => (
                        <SelectItem key={i+1} value={(i+1).toString()}>{i+1}</SelectItem>
                      ))
                    }
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="placement_cell">Ячейка</Label>
                <Select 
                  value={placementForm.cell_number.toString()} 
                  onValueChange={(value) => setPlacementForm({...placementForm, cell_number: parseInt(value)})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {placementForm.warehouse_id && warehouses.find(w => w.id === placementForm.warehouse_id) && 
                      Array.from({length: warehouses.find(w => w.id === placementForm.warehouse_id).cells_per_shelf}, (_, i) => (
                        <SelectItem key={i+1} value={(i+1).toString()}>{i+1}</SelectItem>
                      ))
                    }
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex space-x-2 pt-4">
              <Button type="submit" className="flex-1">
                <Building className="mr-2 h-4 w-4" />
                Разместить груз
              </Button>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setCargoPlacementModal(false);
                  setSelectedCargoForWarehouse(null);
                }}
              >
                Отмена
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Transport Visualization Modal */}
      <Dialog open={transportVisualizationModal} onOpenChange={setTransportVisualizationModal}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              <Truck className="mr-2 h-5 w-5 inline" />
              Схема заполнения транспорта {selectedTransportForVisualization?.transport_number}
            </DialogTitle>
          </DialogHeader>
          
          {transportVisualizationData && (
            <div className="space-y-6">
              {/* Статистика транспорта */}
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{transportVisualizationData.cargo_summary.total_items}</div>
                  <div className="text-sm">Грузов</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{transportVisualizationData.cargo_summary.total_weight} кг</div>
                  <div className="text-sm">Общий вес</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{transportVisualizationData.cargo_summary.fill_percentage_weight}%</div>
                  <div className="text-sm">Заполнение по весу</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">{transportVisualizationData.cargo_summary.total_volume_estimate} м³</div>
                  <div className="text-sm">Примерный объём</div>
                </div>
              </div>

              {/* Прогресс бар заполнения */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Заполнение по весу</span>
                  <span>{transportVisualizationData.cargo_summary.fill_percentage_weight}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full ${
                      transportVisualizationData.cargo_summary.fill_percentage_weight > 100 ? 'bg-red-500' :
                      transportVisualizationData.cargo_summary.fill_percentage_weight > 90 ? 'bg-orange-500' :
                      transportVisualizationData.cargo_summary.fill_percentage_weight > 70 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{width: `${Math.min(transportVisualizationData.cargo_summary.fill_percentage_weight, 100)}%`}}
                  />
                </div>
              </div>

              {/* Схема размещения грузов */}
              <div className="space-y-4">
                <h4 className="font-semibold text-lg">Схема размещения грузов в транспорте</h4>
                <div className="border-2 border-gray-300 rounded-lg p-4 bg-gray-50">
                  <div className="text-center mb-2 text-sm font-medium text-gray-600">
                    ← Передняя часть ({transportVisualizationData.transport.dimensions.length}м x {transportVisualizationData.transport.dimensions.width}м)
                  </div>
                  <div className="grid grid-cols-6 gap-2">
                    {transportVisualizationData.visualization.placement_grid.map((row, rowIndex) =>
                      row.map((cell, cellIndex) => (
                        <div 
                          key={`${rowIndex}-${cellIndex}`}
                          className={`
                            relative h-16 border-2 rounded transition-all
                            ${cell.occupied 
                              ? 'bg-blue-100 border-blue-300 hover:bg-blue-200' 
                              : 'bg-white border-gray-300 border-dashed'
                            }
                          `}
                          title={cell.occupied ? `Груз ${cell.cargo_number}: ${cell.cargo_name} (${cell.weight}кг)` : 'Свободное место'}
                        >
                          {cell.occupied && (
                            <div className="absolute inset-0 p-1 flex flex-col justify-center items-center text-xs">
                              <div className="font-bold text-blue-800">{cell.cargo_number}</div>
                              <div className="text-blue-600 text-center leading-tight">{cell.weight}кг</div>
                            </div>
                          )}
                          <div className="absolute bottom-0 right-0 text-xs text-gray-400 p-1">
                            {cell.position}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                  <div className="text-center mt-2 text-sm font-medium text-gray-600">
                    Задняя часть →
                  </div>
                </div>
              </div>

              {/* Детальный список грузов */}
              <div className="space-y-4">
                <h4 className="font-semibold text-lg">Детальный список грузов ({transportVisualizationData.cargo_summary.total_items})</h4>
                <div className="max-h-64 overflow-y-auto border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>№ Груза</TableHead>
                        <TableHead>Наименование</TableHead>
                        <TableHead>Вес (кг)</TableHead>
                        <TableHead>Получатель</TableHead>
                        <TableHead>Позиция</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {transportVisualizationData.cargo_summary.cargo_list.map((cargo, index) => (
                        <TableRow key={cargo.id}>
                          <TableCell className="font-medium">{cargo.cargo_number}</TableCell>
                          <TableCell>{cargo.cargo_name}</TableCell>
                          <TableCell>{cargo.weight}</TableCell>
                          <TableCell>{cargo.recipient_name}</TableCell>
                          <TableCell>{Math.floor(index / 6) + 1}-{(index % 6) + 1}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* QR/Number Cargo Placement Modal */}
      <Dialog open={qrPlacementModal} onOpenChange={setQrPlacementModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              <QrCode className="mr-2 h-5 w-5 inline" />
              Размещение груза по номеру/QR
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleQrCargoPlacement} className="space-y-4">
            <div className="p-3 bg-purple-50 rounded-lg">
              <h5 className="font-medium text-purple-800 mb-2">Размещение груза</h5>
              <p className="text-sm text-purple-700">
                Склад будет выбран автоматически на основе ваших привязок. Вы должны указать конкретную ячейку для размещения вручную или через QR код ячейки.
              </p>
            </div>

            <div>
              <Label htmlFor="cargo_number">Номер груза</Label>
              <Input
                id="cargo_number"
                value={qrPlacementForm.cargo_number}
                onChange={(e) => setQrPlacementForm({...qrPlacementForm, cargo_number: e.target.value})}
                placeholder="1234"
                required={!qrPlacementForm.qr_data}
              />
            </div>

            <div className="text-center text-sm text-gray-500">или</div>

            <div>
              <Label htmlFor="qr_data">QR код груза</Label>
              <textarea
                id="qr_data"
                className="w-full mt-2 p-3 border rounded-md"
                rows="3"
                value={qrPlacementForm.qr_data}
                onChange={(e) => setQrPlacementForm({...qrPlacementForm, qr_data: e.target.value})}
                placeholder="Вставьте QR код груза..."
                required={!qrPlacementForm.cargo_number}
              />
            </div>

            <div className="border-t pt-4">
              <Label>Размещение в ячейке</Label>
              
              <div className="mt-2">
                <Label htmlFor="cell_qr_data">QR код ячейки склада</Label>
                <textarea
                  id="cell_qr_data"
                  className="w-full mt-2 p-3 border rounded-md"
                  rows="3"
                  value={qrPlacementForm.cell_qr_data}
                  onChange={(e) => setQrPlacementForm({...qrPlacementForm, cell_qr_data: e.target.value})}
                  placeholder="Отсканируйте QR код ячейки склада..."
                />
              </div>

              <div className="text-center text-sm text-gray-500 my-2">или укажите координаты вручную</div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label htmlFor="manual_block">Блок</Label>
                  <Input
                    id="manual_block"
                    type="number"
                    min="1"
                    value={qrPlacementForm.block_number}
                    onChange={(e) => setQrPlacementForm({...qrPlacementForm, block_number: e.target.value})}
                    placeholder="1"
                  />
                </div>
                <div>
                  <Label htmlFor="manual_shelf">Полка</Label>
                  <Input
                    id="manual_shelf"
                    type="number"
                    min="1"
                    value={qrPlacementForm.shelf_number}
                    onChange={(e) => setQrPlacementForm({...qrPlacementForm, shelf_number: e.target.value})}
                    placeholder="1"
                  />
                </div>
                <div>
                  <Label htmlFor="manual_cell">Ячейка</Label>
                  <Input
                    id="manual_cell"
                    type="number"
                    min="1"
                    value={qrPlacementForm.cell_number}
                    onChange={(e) => setQrPlacementForm({...qrPlacementForm, cell_number: e.target.value})}
                    placeholder="1"
                  />
                </div>
              </div>
            </div>

            <div className="flex space-x-2 pt-4">
              <Button type="submit" className="flex-1">
                <Building className="mr-2 h-4 w-4" />
                Разместить груз
              </Button>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setQrPlacementModal(false);
                  setQrPlacementForm({
                    cargo_number: '',
                    qr_data: '',
                    cell_qr_data: '',
                    block_number: 1,
                    shelf_number: 1,
                    cell_number: 1
                  });
                }}
              >
                Отмена
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Interwarehouse Transport Modal */}
      <Dialog open={interwarehouseTransportModal} onOpenChange={setInterwarehouseTransportModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              <Truck className="mr-2 h-5 w-5 inline" />
              Создание межскладского транспорта
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleCreateInterwarehouseTransport} className="space-y-4">
            <div className="p-3 bg-blue-50 rounded-lg">
              <h5 className="font-medium text-blue-800 mb-2">Межскладская перевозка</h5>
              <p className="text-sm text-blue-700">
                Создайте транспорт для перевозки грузов между вашими складами. Доступны только склады, к которым у вас есть доступ.
              </p>
            </div>

            <div>
              <Label htmlFor="source_warehouse">Исходный склад</Label>
              <Select 
                value={interwarehouseForm.source_warehouse_id} 
                onValueChange={(value) => setInterwarehouseForm({...interwarehouseForm, source_warehouse_id: value})}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите исходный склад" />
                </SelectTrigger>
                <SelectContent>
                  {(user?.role === 'admin' ? warehouses : operatorWarehouses).map((warehouse) => (
                    <SelectItem key={warehouse.id} value={warehouse.id}>
                      {warehouse.name} ({warehouse.location})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="destination_warehouse">Целевой склад</Label>
              <Select 
                value={interwarehouseForm.destination_warehouse_id} 
                onValueChange={(value) => setInterwarehouseForm({...interwarehouseForm, destination_warehouse_id: value})}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Выберите целевой склад" />
                </SelectTrigger>
                <SelectContent>
                  {(user?.role === 'admin' ? warehouses : operatorWarehouses)
                    .filter(w => w.id !== interwarehouseForm.source_warehouse_id)
                    .map((warehouse) => (
                      <SelectItem key={warehouse.id} value={warehouse.id}>
                        {warehouse.name} ({warehouse.location})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="iw_driver_name">ФИО водителя</Label>
              <Input
                id="iw_driver_name"
                value={interwarehouseForm.driver_name}
                onChange={(e) => setInterwarehouseForm({...interwarehouseForm, driver_name: e.target.value})}
                placeholder="Иван Иванов"
                required
              />
            </div>

            <div>
              <Label htmlFor="iw_driver_phone">Телефон водителя</Label>
              <Input
                id="iw_driver_phone"
                value={interwarehouseForm.driver_phone}
                onChange={(e) => setInterwarehouseForm({...interwarehouseForm, driver_phone: e.target.value})}
                placeholder="+7 (999) 123-45-67"
                required
              />
            </div>

            <div>
              <Label htmlFor="iw_capacity">Грузоподъемность (кг)</Label>
              <Input
                id="iw_capacity"
                type="number"
                min="100"
                step="50"
                value={interwarehouseForm.capacity_kg}
                onChange={(e) => setInterwarehouseForm({...interwarehouseForm, capacity_kg: parseInt(e.target.value)})}
                required
              />
            </div>

            <div className="flex space-x-2 pt-4">
              <Button type="submit" className="flex-1">
                <Truck className="mr-2 h-4 w-4" />
                Создать транспорт
              </Button>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setInterwarehouseTransportModal(false);
                  setInterwarehouseForm({
                    source_warehouse_id: '',
                    destination_warehouse_id: '',
                    driver_name: '',
                    driver_phone: '',
                    capacity_kg: 1000
                  });
                }}
              >
                Отмена
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;