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
import DataPagination from './components/DataPagination'; // Новый компонент пагинации
import { 
  Truck, Package, Users, Bell, Search, Plus, Edit, Trash2, CheckCircle, 
  Clock, MapPin, User, Shield, Warehouse, Menu, X, Building, 
  DollarSign, FileText, Grid3X3, Package2, Home, CreditCard, Printer, Zap, MessageCircle,
  QrCode, Camera, Download, Calculator, ShoppingCart, RefreshCw, Eye, XCircle, Save, Filter,
  ArrowUp, Ban, Settings, Copy, Minus
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeSection, setActiveSection] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [cargo, setCargo] = useState([]);
  const [users, setUsers] = useState([]);
  const [usersPagination, setUsersPagination] = useState({}); // Пагинация для пользователей
  const [usersPage, setUsersPage] = useState(1);
  const [usersPerPage, setUsersPerPage] = useState(25);
  const [warehouses, setWarehouses] = useState([]);
  const [warehouseCargo, setWarehouseCargo] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [trackingNumber, setTrackingNumber] = useState('');
  const [trackingResult, setTrackingResult] = useState(null);

  // Новые состояния для клиентского дашборда (Функция 1)
  const [clientDashboard, setClientDashboard] = useState(null);
  const [clientCargo, setClientCargo] = useState([]);
  const [clientCargoDetails, setClientCargoDetails] = useState(null);

  // Новые состояния для создания оператора (Функция 2)
  const [operatorCreateForm, setOperatorCreateForm] = useState({
    full_name: '',
    phone: '',
    address: '',
    password: '',
    warehouse_id: ''
  });
  const [operatorCreationModal, setOperatorCreationModal] = useState(false);
  const [allOperators, setAllOperators] = useState([]);

  // Новые состояния для оформления груза клиентами
  const [cargoOrderForm, setCargoOrderForm] = useState({
    cargo_name: '',
    description: '',
    weight: '',
    declared_value: '80', // По умолчанию для Москва → Душанбе
    recipient_full_name: '',
    recipient_phone: '',
    recipient_address: '',
    recipient_city: '',
    route: 'moscow_dushanbe',
    delivery_type: 'standard',
    insurance_requested: false,
    insurance_value: '',
    packaging_service: false,
    home_pickup: false,
    home_delivery: false,
    fragile: false,
    temperature_sensitive: false,
    special_instructions: ''
  });
  const [deliveryOptions, setDeliveryOptions] = useState(null);
  const [costCalculation, setCostCalculation] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [cargoOrderResult, setCargoOrderResult] = useState(null);

  // НОВЫЕ ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ ЗАКАЗАМИ КЛИЕНТОВ

  // Функция для установки объявленной стоимости по умолчанию в зависимости от маршрута
  const getDefaultDeclaredValue = (route) => {
    switch(route) {
      case 'moscow_khujand':
        return '60'; // Москва → Худжанд: 60 рублей
      case 'moscow_dushanbe':
        return '80'; // Москва → Душанбе: 80 рублей
      case 'moscow_kulob':
        return '80'; // Москва → Кулоб: 80 рублей 
      case 'moscow_kurgantyube':
        return '80'; // Москва → Курган-Тюбе: 80 рублей
      case 'moscow_to_tajikistan':
        return '80'; // По умолчанию для общего маршрута
      default:
        return '80'; // По умолчанию
    }
  };

  // Обработчик изменения маршрута с автоматическим обновлением стоимости
  const handleRouteChange = (newRoute) => {
    const defaultValue = getDefaultDeclaredValue(newRoute);
    setCargoOrderForm(prevForm => ({
      ...prevForm,
      route: newRoute,
      declared_value: defaultValue
    }));
  };

  // Новые состояния для управления заказами клиентов
  const [pendingOrders, setPendingOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderDetailsModal, setOrderDetailsModal] = useState(false);
  const [editOrderModal, setEditOrderModal] = useState(false);
  const [newOrdersCount, setNewOrdersCount] = useState(0);
  const [orderEditForm, setOrderEditForm] = useState({
    sender_full_name: '',
    sender_phone: '',
    recipient_full_name: '',
    recipient_phone: '',
    recipient_address: '',
    pickup_address: '',
    cargo_name: '',
    weight: '',
    declared_value: '',
    description: '',
    route: '',
    admin_notes: ''
  });

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
    weight: '',  // Сохраняем для совместимости со старой формой
    cargo_name: '',  // Сохраняем для совместимости со старой формой
    declared_value: '',  // Теперь будет использоваться как price_per_kg для старой формы
    description: '',
    route: 'moscow_to_tajikistan',
    // Новые поля для множественных грузов с индивидуальными ценами
    cargo_items: [{ cargo_name: '', weight: '', price_per_kg: '' }],  // Каждый груз имеет свою цену
    price_per_kg: '',  // Общая цена за кг (для совместимости)
    use_multi_cargo: false  // Флаг для переключения между режимами
  });
  // Operator cargo management states
  const [operatorCargo, setOperatorCargo] = useState([]);
  
  // Calculator states for multi-cargo functionality with individual prices
  const [totalWeight, setTotalWeight] = useState(0);
  const [totalCost, setTotalCost] = useState(0);
  const [cargoBreakdown, setCargoBreakdown] = useState([]);  // Детальная разбивка по каждому грузу

  // Personal dashboard states
  const [personalDashboardData, setPersonalDashboardData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  
  // Role management states
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [selectedUserForRole, setSelectedUserForRole] = useState(null);
  const [newRole, setNewRole] = useState('');

  // Advanced search states
  const [advancedSearchOpen, setAdvancedSearchOpen] = useState(false);
  const [searchFilters, setSearchFilters] = useState({
    cargo_status: '',
    payment_status: '',
    processing_status: '',
    route: '',
    sender_phone: '',
    recipient_phone: '',
    date_from: '',
    date_to: '',
    user_role: '',
    user_status: null,
    sort_by: 'created_at',
    sort_order: 'desc'
  });
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchTime, setSearchTime] = useState(0);

  // Profile management states
  const [showOperatorProfile, setShowOperatorProfile] = useState(false);
  const [showUserProfile, setShowUserProfile] = useState(false);
  const [selectedOperatorProfile, setSelectedOperatorProfile] = useState(null);
  const [selectedUserProfile, setSelectedUserProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  
  // Quick cargo creation states
  const [showQuickCargoModal, setShowQuickCargoModal] = useState(false);
  const [quickCargoForm, setQuickCargoForm] = useState({
    sender_id: '',
    recipient_data: {},
    cargo_items: [{ cargo_name: '', weight: '', price_per_kg: '' }],
    route: 'moscow_to_tajikistan',
    description: ''
  });
  const [frequentRecipients, setFrequentRecipients] = useState([]);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [operatorCargoFilter, setOperatorCargoFilter] = useState(''); // Фильтр для списка грузов
  const [operatorCargoPagination, setOperatorCargoPagination] = useState({}); // Пагинация для списка грузов
  const [operatorCargoPage, setOperatorCargoPage] = useState(1);
  const [operatorCargoPerPage, setOperatorCargoPerPage] = useState(25);
  
  const [availableCargo, setAvailableCargo] = useState([]);
  const [availableCargoForPlacement, setAvailableCargoForPlacement] = useState([]); // Грузы для размещения
  const [availableCargoPagination, setAvailableCargoPagination] = useState({}); // Пагинация для размещения
  const [availableCargoPage, setAvailableCargoPage] = useState(1);
  const [availableCargoPerPage, setAvailableCargoPerPage] = useState(25);
  
  const [selectedCargoForDetailView, setSelectedCargoForDetailView] = useState(null); // Выбранный груз для просмотра деталей
  const [cargoDetailsModal, setCargoDetailsModal] = useState(false); // Модальное окно деталей груза
  const [quickPlacementModal, setQuickPlacementModal] = useState(false); // Быстрое размещение
  const [quickPlacementForm, setQuickPlacementForm] = useState({
    block_number: 1,
    shelf_number: 1,
    cell_number: 1
  });
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
    declared_value: '80', // По умолчанию для общего маршрута moscow_to_tajikistan
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
  
  // Состояние для предотвращения множественных logout'ов
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  
  // Состояние для отслеживания процесса логина
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Новые состояния для расширенного профиля пользователя
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [editProfileForm, setEditProfileForm] = useState({
    full_name: '',
    phone: '',
    email: '',
    address: ''
  });
  const [showRepeatOrderModal, setShowRepeatOrderModal] = useState(false);
  const [repeatOrderData, setRepeatOrderData] = useState(null);
  const [repeatOrderForm, setRepeatOrderForm] = useState({
    cargo_items: [{ cargo_name: '', weight: '', price_per_kg: '' }],
    recipient_full_name: '',
    recipient_phone: '',
    recipient_address: '',
    route: 'moscow_dushanbe',
    delivery_type: 'standard',
    insurance_requested: false,
    special_instructions: '',
    use_multi_cargo: true
  });
  
  // Состояния для мульти-груз калькулятора в повторном заказе
  const [repeatOrderTotalWeight, setRepeatOrderTotalWeight] = useState(0);
  const [repeatOrderTotalCost, setRepeatOrderTotalCost] = useState(0);
  const [repeatOrderBreakdown, setRepeatOrderBreakdown] = useState([]);

  // Новые состояния для админ функций
  const [showAdminEditUser, setShowAdminEditUser] = useState(false);
  const [adminEditUserForm, setAdminEditUserForm] = useState({
    id: '',
    full_name: '',
    phone: '',
    email: '',
    address: '',
    role: 'user',
    is_active: true
  });
  const [selectedUserForEdit, setSelectedUserForEdit] = useState(null);
  
  // Состояния для повторного заказа админом/оператором
  const [showAdminRepeatOrderModal, setShowAdminRepeatOrderModal] = useState(false);
  const [adminRepeatOrderData, setAdminRepeatOrderData] = useState(null);
  const [adminRepeatOrderForm, setAdminRepeatOrderForm] = useState({
    sender_id: '',
    sender_full_name: '',
    sender_phone: '',
    cargo_items: [{ cargo_name: '', weight: '', price_per_kg: '' }],
    recipient_full_name: '',
    recipient_phone: '',
    recipient_address: '',
    route: 'moscow_dushanbe',
    delivery_type: 'standard',
    insurance_requested: false,
    special_instructions: '',
    use_multi_cargo: true
  });
  
  // Состояния для мульти-груз калькулятора админа/оператора
  const [adminRepeatOrderTotalWeight, setAdminRepeatOrderTotalWeight] = useState(0);
  const [adminRepeatOrderTotalCost, setAdminRepeatOrderTotalCost] = useState(0);
  const [adminRepeatOrderBreakdown, setAdminRepeatOrderBreakdown] = useState([]);

  // Состояние для отслеживания автозаполнения из профиля
  const [isFilledFromProfile, setIsFilledFromProfile] = useState(false);
  const [profileSourceUser, setProfileSourceUser] = useState(null);

  const showAlert = (message, type = 'info') => {
    const id = Date.now();
    setAlerts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setAlerts(prev => prev.filter(alert => alert.id !== id));
    }, 5000);
  };

  const apiCall = async (endpoint, method = 'GET', data = null, params = null, retryCount = 0) => {
    try {
      // Build URL with query parameters if provided
      let url = `${BACKEND_URL}${endpoint}`;
      if (params) {
        const urlParams = new URLSearchParams(params);
        url += `?${urlParams.toString()}`;
      }

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

      const response = await fetch(url, config);
      const result = await response.json();

      if (!response.ok) {
        // Обработка 401 ошибки (unauthorized) - токен истек или невалиден
        if (response.status === 401 && !isLoggingOut && !isLoggingIn) {
          console.log('Received 401 response, checking token validity...');
          
          // Проверяем, действительно ли токен истек на клиенте
          if (token && !isTokenValid(token)) {
            console.log('Token is expired client-side, logging out');
            handleLogout();
            throw new Error('Session expired');
          } else if (token && isTokenValid(token)) {
            // Токен валиден на клиенте, но сервер вернул 401
            // Это может быть временная проблема - попробуем еще раз
            console.log('Token appears valid client-side but server returned 401, will retry once...');
            
            // Повторный запрос только один раз для избежания бесконечных циклов
            if (!config.retryCount) {
              config.retryCount = 1;
              const retryResponse = await fetch(url, config);
              if (retryResponse.ok) {
                const retryResult = await retryResponse.json();
                return retryResult;
              } else if (retryResponse.status === 401) {
                // Если повторный запрос тоже вернул 401, то токен действительно невалиден
                console.log('Retry also returned 401, token is invalid on server');
                handleLogout();
                throw new Error('Session expired');
              }
            }
          } else if (!isLoggingIn) {
            // Нет токена и это не процесс логина
            console.log('No token available and not logging in, logging out');
            handleLogout();
            throw new Error('Authentication required');
          }
        }
        
        // Правильная обработка detail - может быть строкой или массивом объектов
        let errorMessage = 'Произошла ошибка';
        
        if (result.detail) {
          if (Array.isArray(result.detail)) {
            // Если detail - массив объектов ошибок валидации, извлекаем msg из каждого
            errorMessage = result.detail.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
          } else if (typeof result.detail === 'string') {
            // Если detail - строка, используем как есть
            errorMessage = result.detail;
          } else {
            // Если detail - объект, попытаемся получить message или преобразуем в строку
            errorMessage = result.detail.message || JSON.stringify(result.detail);
          }
        } else if (result.message) {
          errorMessage = result.message;
        }
        
        throw new Error(errorMessage);
      }

      return result;
    } catch (error) {
      // Показываем alert только если это не ошибка истечения сессии
      if (error.message !== 'Session expired') {
        showAlert(error.message, 'error');
      }
      throw error;
    }
  };

  // Новые функции для клиентского дашборда (Функция 1)
  const fetchClientDashboard = async () => {
    try {
      const data = await apiCall('/api/client/dashboard');
      setClientDashboard(data);
    } catch (error) {
      console.error('Error fetching client dashboard:', error);
    }
  };

  const fetchClientCargo = async (status = null) => {
    try {
      const params = status ? `?status=${status}` : '';
      const data = await apiCall(`/api/client/cargo${params}`);
      setClientCargo(data.cargo || []);
    } catch (error) {
      console.error('Error fetching client cargo:', error);
    }
  };

  const fetchClientCargoDetails = async (cargoId) => {
    try {
      const data = await apiCall(`/api/client/cargo/${cargoId}/details`);
      setClientCargoDetails(data);
    } catch (error) {
      console.error('Error fetching client cargo details:', error);
    }
  };

  // Новые функции для создания операторов (Функция 2)
  const fetchAllOperators = async () => {
    try {
      const data = await apiCall('/api/admin/operators');
      setAllOperators(data.operators || []);
    } catch (error) {
      console.error('Error fetching operators:', error);
    }
  };

  const handleCreateOperator = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/admin/create-operator', 'POST', operatorCreateForm);
      
      // Сброс формы
      setOperatorCreateForm({
        full_name: '',
        phone: '',
        address: '',
        password: '',
        warehouse_id: ''
      });
      
      // Обновление данных
      fetchAllOperators();
      fetchOperatorWarehouseBindings();
      fetchUsersByRole();
      
      // Показать уведомление об успехе
      alert('Оператор успешно создан!');
      
    } catch (error) {
      console.error('Error creating operator:', error);
      alert(error.message || 'Ошибка создания оператора');
    }
  };

  // Новые функции для оформления груза
  const fetchDeliveryOptions = async () => {
    try {
      const data = await apiCall('/api/client/cargo/delivery-options');
      setDeliveryOptions(data);
    } catch (error) {
      console.error('Error fetching delivery options:', error);
    }
  };

  const calculateCargoCost = async () => {
    if (!cargoOrderForm.weight || !cargoOrderForm.declared_value || !cargoOrderForm.cargo_name) {
      return;
    }

    setIsCalculating(true);
    try {
      // Подготавливаем данные для расчета
      const calculationData = {
        ...cargoOrderForm,
        weight: parseFloat(cargoOrderForm.weight),
        declared_value: parseFloat(cargoOrderForm.declared_value),
        insurance_value: cargoOrderForm.insurance_requested ? parseFloat(cargoOrderForm.insurance_value || cargoOrderForm.declared_value) : null
      };

      const data = await apiCall('/api/client/cargo/calculate', 'POST', calculationData);
      setCostCalculation(data);
    } catch (error) {
      console.error('Error calculating cost:', error);
      alert('Ошибка расчета стоимости: ' + (error.message || 'Неизвестная ошибка'));
    } finally {
      setIsCalculating(false);
    }
  };

  const handleCreateCargoOrder = async (e) => {
    e.preventDefault();
    
    if (!costCalculation) {
      showAlert('Сначала рассчитайте стоимость доставки', 'error');
      return;
    }

    try {
      // Подготавливаем данные для создания груза
      const orderData = {
        ...cargoOrderForm,
        weight: parseFloat(cargoOrderForm.weight),
        declared_value: parseFloat(cargoOrderForm.declared_value),
        insurance_value: cargoOrderForm.insurance_requested ? parseFloat(cargoOrderForm.insurance_value || cargoOrderForm.declared_value) : null
      };

      const result = await apiCall('/api/client/cargo/create', 'POST', orderData);
      setCargoOrderResult(result);
      
      // Сброс формы
      setCargoOrderForm({
        cargo_name: '',
        description: '',
        weight: '',
        declared_value: getDefaultDeclaredValue('moscow_dushanbe'), // Используем значение по умолчанию
        recipient_full_name: '',
        recipient_phone: '',
        recipient_address: '',
        recipient_city: '',
        route: 'moscow_dushanbe',
        delivery_type: 'standard',
        insurance_requested: false,
        insurance_value: '',
        packaging_service: false,
        home_pickup: false,
        home_delivery: false,
        fragile: false,
        temperature_sensitive: false,
        special_instructions: ''
      });
      setCostCalculation(null);
      
      // Обновляем данные клиента
      fetchClientDashboard();
      fetchClientCargo();
      
      // Показываем успешное сообщение
      showAlert(`Груз успешно оформлен! Номер: ${result.cargo_number}, Трекинг: ${result.tracking_code}`, 'success');
      
    } catch (error) {
      console.error('Error creating cargo order:', error);
      
      // Правильная обработка ошибок
      let errorMessage = 'Неизвестная ошибка при оформлении груза';
      
      if (error.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error.detail) {
        errorMessage = error.detail;
      }
      
      showAlert('Ошибка оформления груза: ' + errorMessage, 'error');
    }
  };

  useEffect(() => {
    if (token && !isLoggingOut && !isLoggingIn) {
      // Проверяем валидность токена перед использованием
      if (isTokenValid(token)) {
        // Попытка получить информацию о пользователе при загрузке
        // Добавляем небольшую задержку, чтобы избежать race condition
        setTimeout(() => {
          if (token && !isLoggingIn) {
            fetchUserData();
          }
        }, 500);
      } else {
        // Токен истек, очищаем его
        console.log('Token expired on startup, clearing session');
        handleLogout();
        showAlert('Ваша сессия истекла. Пожалуйста, войдите в систему снова.', 'warning');
      }
    }
  }, [token]);

  // Периодическая проверка валидности токена
  useEffect(() => {
    if (token && user && !isLoggingOut && !isLoggingIn) {
      const interval = setInterval(() => {
        if (!isTokenValid(token)) {
          console.log('Token expired during session, logging out');
          handleLogout();
        }
      }, 60000); // Проверяем каждую минуту

      return () => clearInterval(interval);
    }
  }, [token, user, isLoggingOut, isLoggingIn]);

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
        fetchAllOperators(); // Функция 2 - загрузка операторов для админа
        fetchNewOrdersCount(); // Загрузка количества новых заказов
      } else if (user.role === 'warehouse_operator') {
        fetchWarehouseCargo();
        fetchWarehouses();
        fetchOperatorCargo('', 1, 25);
        fetchAvailableCargoForPlacement(1, 25); // Добавляем загрузку грузов для размещения
        fetchUnpaidCargo();
        fetchPaymentHistory();
        fetchCargoRequests();
        fetchSystemNotifications();
        fetchTransportsList(); // Обновлено для операторов
        fetchArrivedTransports();
        fetchOperatorWarehouses(); // Добавлено для операторов
        fetchNewOrdersCount(); // Загрузка количества новых заказов для операторов
      } else {
        fetchMyCargo();
        fetchMyRequests();
        fetchSystemNotifications();
        // Новые функции для клиентского дашборда (Функция 1)
        fetchClientDashboard();
        fetchClientCargo();
        // Загружаем опции доставки для оформления грузов
        fetchDeliveryOptions();
      }
    }
  }, [user]);

  // Функция загрузки данных личного кабинета
  const fetchPersonalDashboard = async () => {
    setDashboardLoading(true);
    try {
      const response = await apiCall('/api/user/dashboard', 'GET');
      setPersonalDashboardData(response);
    } catch (error) {
      console.error('Error fetching personal dashboard:', error);
      showAlert('Ошибка загрузки личного кабинета', 'error');
    } finally {
      setDashboardLoading(false);
    }
  };

  // Функция управления ролями
  const handleRoleChange = async () => {
    if (!selectedUserForRole || !newRole) return;
    
    try {
      await apiCall(`/api/admin/users/${selectedUserForRole.id}/role`, 'PUT', {
        user_id: selectedUserForRole.id,
        new_role: newRole
      });
      
      showAlert(`Роль пользователя изменена на ${getRoleLabel(newRole)}`, 'success');
      setShowRoleModal(false);
      setSelectedUserForRole(null);
      setNewRole('');
      fetchUsers(); // Обновляем список пользователей
    } catch (error) {
      showAlert(error.message || 'Ошибка изменения роли', 'error');
    }
  };

  // Открытие модального окна изменения роли
  const openRoleModal = (user) => {
    setSelectedUserForRole(user);
    setNewRole(user.role);
    setShowRoleModal(true);
  };

  const fetchUserData = async () => {
    try {
      // Get user data from backend using the token
      const userData = await apiCall('/api/auth/me', 'GET');
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      // Session clearing is now handled in apiCall function
      // No duplicate clearing logic needed here
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

  const fetchUsers = async (page = usersPage, perPage = usersPerPage) => {
    try {
      const params = {
        page: page,
        per_page: perPage
      };
      
      const response = await apiCall('/api/admin/users', 'GET', null, params);
      
      // Проверяем новый формат ответа с пагинацией
      if (response.items) {
        setUsers(response.items); // Используем items из пагинированного ответа
        setUsersPagination(response.pagination);
      } else {
        // Обратная совместимость со старым форматом
        setUsers(response);
        setUsersPagination({});
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      setUsers([]); // Устанавливаем пустой массив в случае ошибки
      setUsersPagination({});
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

  const fetchAvailableCargoForPlacement = async (page = availableCargoPage, perPage = availableCargoPerPage) => {
    try {
      const params = {
        page: page,
        per_page: perPage
      };
      
      const response = await apiCall('/api/operator/cargo/available-for-placement', 'GET', null, params);
      
      // Проверяем новый формат ответа с пагинацией
      if (response.items) {
        setAvailableCargoForPlacement(response.items);
        setAvailableCargoPagination(response.pagination);
      } else {
        // Обратная совместимость со старым форматом
        setAvailableCargoForPlacement(response.cargo_list || response);
        setAvailableCargoPagination({});
      }
    } catch (error) {
      console.error('Error fetching available cargo for placement:', error);
      setAvailableCargoForPlacement([]);
      setAvailableCargoPagination({});
    }
  };

  // Обработчики пагинации для списка грузов
  const handleOperatorCargoPageChange = (newPage) => {
    setOperatorCargoPage(newPage);
    fetchOperatorCargo(operatorCargoFilter, newPage, operatorCargoPerPage);
  };

  const handleOperatorCargoPerPageChange = (newPerPage) => {
    const perPage = parseInt(newPerPage);
    setOperatorCargoPerPage(perPage);
    setOperatorCargoPage(1); // Сбрасываем на первую страницу
    fetchOperatorCargo(operatorCargoFilter, 1, perPage);
  };

  // Обработчики пагинации для пользователей
  const handleUsersPageChange = (newPage) => {
    setUsersPage(newPage);
    fetchUsers(newPage, usersPerPage);
  };

  const handleUsersPerPageChange = (newPerPage) => {
    const perPage = parseInt(newPerPage);
    setUsersPerPage(perPage);
    setUsersPage(1); // Сбрасываем на первую страницу
    fetchUsers(1, perPage);
  };

  // Обработчики пагинации для размещения грузов
  const handleAvailableCargoPageChange = (newPage) => {
    setAvailableCargoPage(newPage);
    fetchAvailableCargoForPlacement(newPage, availableCargoPerPage);
  };

  const handleAvailableCargoPerPageChange = (newPerPage) => {
    const perPage = parseInt(newPerPage);
    setAvailableCargoPerPage(perPage);
    setAvailableCargoPage(1); // Сбрасываем на первую страницу
    fetchAvailableCargoForPlacement(1, perPage);
  };

  const fetchWarehouseLayoutWithCargo = async (warehouseId) => {
    try {
      console.log('Fetching warehouse layout for ID:', warehouseId);
      const response = await apiCall(`/api/warehouses/${warehouseId}/layout-with-cargo`);
      console.log('Warehouse layout response:', response);
      setWarehouseLayout(response);
      setSelectedWarehouseForLayout(warehouseId);
    } catch (error) {
      console.error('Error fetching warehouse layout with cargo:', error);
      showAlert('Ошибка при загрузке схемы склада: ' + error.message, 'error');
    }
  };

  const handleCargoMove = async () => {
    if (!selectedCargoForWarehouse) return;
    
    try {
      const moveData = {
        cargo_id: selectedCargoForWarehouse.id,
        from_block: selectedCargoForWarehouse.block_number,
        from_shelf: selectedCargoForWarehouse.shelf_number,
        from_cell: selectedCargoForWarehouse.cell_number,
        to_block: cargoMoveForm.to_block,
        to_shelf: cargoMoveForm.to_shelf,
        to_cell: cargoMoveForm.to_cell
      };

      const response = await apiCall(`/api/warehouses/${selectedWarehouseForLayout}/move-cargo`, 'POST', moveData);
      
      showAlert(`Груз ${response.cargo_number} успешно перемещен с ${response.old_location} на ${response.new_location}`, 'success');
      
      // Обновляем схему склада
      fetchWarehouseLayoutWithCargo(selectedWarehouseForLayout);
      
      // Закрываем модальное окно
      setCargoMoveModal(false);
      setSelectedCargoForWarehouse(null);
      setCargoMoveForm({
        to_block: 1,
        to_shelf: 1,
        to_cell: 1
      });
      
    } catch (error) {
      console.error('Error moving cargo:', error);
      showAlert('Ошибка при перемещении груза: ' + error.message, 'error');
    }
  };

  const handleCleanupTestData = async () => {
    if (!confirm('⚠️ ВНИМАНИЕ!\n\nЭто действие удалит ВСЕ тестовые данные из системы:\n- Тестовых пользователей\n- Тестовые грузы и заявки\n- Связанные уведомления\n- Данные о ячейках\n\nДействие НЕОБРАТИМО!\n\nВы уверены, что хотите продолжить?')) {
      return;
    }
    
    try {
      const response = await apiCall('/api/admin/cleanup-test-data', 'POST');
      
      // Показываем детальный отчет об очистке
      const report = response.cleanup_report;
      const summaryMessage = `
🧹 Очистка тестовых данных завершена!

📊 Отчет об удалении:
• Пользователи: ${report.users_deleted}
• Заявки на грузы: ${report.cargo_requests_deleted}  
• Грузы операторов: ${report.operator_cargo_deleted}
• Грузы пользователей: ${report.user_cargo_deleted}
• Неоплаченные заказы: ${report.unpaid_orders_deleted}
• Уведомления: ${report.notifications_deleted}
• Ячейки склада: ${report.warehouse_cells_deleted}

Время очистки: ${new Date(response.cleanup_time).toLocaleString('ru-RU')}
      `.trim();
      
      showAlert(summaryMessage, 'success');
      
      // Обновляем списки
      fetchOperatorCargo(operatorCargoFilter, operatorCargoPage, operatorCargoPerPage);
      fetchAvailableCargoForPlacement(availableCargoPage, availableCargoPerPage);
      fetchUsersByRole();
      fetchNotifications();
      fetchUnpaidCargo();
      
    } catch (error) {
      console.error('Error cleaning test data:', error);
      showAlert('Ошибка при очистке тестовых данных: ' + error.message, 'error');
    }
  };

  const handleQuickPlacement = async (cargoId) => {
    try {
      const response = await apiCall(`/api/cargo/${cargoId}/quick-placement`, 'POST', quickPlacementForm);
      showAlert(`Груз успешно размещен: ${response.location}`, 'success');
      
      // Обновляем списки
      fetchOperatorCargo(operatorCargoFilter);
      fetchAvailableCargoForPlacement();
      
      // Закрываем модальные окна
      setQuickPlacementModal(false);
      setSelectedCargoForDetailView(null);
      
      // Сбрасываем форму
      setQuickPlacementForm({
        block_number: 1,
        shelf_number: 1,
        cell_number: 1
      });
    } catch (error) {
      console.error('Error placing cargo:', error);
      showAlert('Ошибка при размещении груза: ' + error.message, 'error');
    }
  };

  const handlePaymentAcceptance = async (cargoId, cargoNumber) => {
    try {
      // Обновляем статус на оплачено
      await apiCall(`/api/cargo/${cargoId}/processing-status`, 'PUT', { new_status: 'paid' });
      
      showAlert(`✅ Оплата принята для груза ${cargoNumber}`, 'success');
      showAlert('📦 Груз автоматически перемещен в раздел "Ожидает размещение"', 'info');
      
      // Обновляем все списки
      fetchOperatorCargo(operatorCargoFilter);
      fetchAvailableCargoForPlacement();
      
    } catch (error) {
      console.error('Error accepting payment:', error);
      showAlert('Ошибка при принятии оплаты: ' + error.message, 'error');
    }
  };

  const updateCargoProcessingStatus = async (cargoId, newStatus) => {
    try {
      await apiCall(`/api/cargo/${cargoId}/processing-status`, 'PUT', { new_status: newStatus });
      showAlert(`Статус груза успешно обновлен: ${getProcessingStatusLabel(newStatus)}`, 'success');
      
      // Обновляем все списки для синхронизации
      fetchOperatorCargo(operatorCargoFilter, operatorCargoPage, operatorCargoPerPage);
      fetchAvailableCargoForPlacement(availableCargoPage, availableCargoPerPage); // Обновляем список для размещения
      
      // Если груз стал оплаченным, показываем сообщение о перемещении
      if (newStatus === 'paid') {
        showAlert('Груз переведен в раздел "Ожидает размещение"', 'info');
      }
    } catch (error) {
      console.error('Error updating cargo processing status:', error);
      showAlert('Ошибка при обновлении статуса груза: ' + error.message, 'error');
    }
  };

  const getProcessingStatusLabel = (status) => {
    const labels = {
      'payment_pending': 'Ожидает оплаты',
      'paid': 'Оплачен',
      'invoice_printed': 'Накладная напечатана',
      'placed': 'Размещен на складе'
    };
    return labels[status] || status;
  };

  const getProcessingStatusBadgeVariant = (status) => {
    const variants = {
      'payment_pending': 'destructive',
      'paid': 'default',
      'invoice_printed': 'secondary',
      'placed': 'outline'
    };
    return variants[status] || 'outline';
  };

  const fetchOperatorCargo = async (filterStatus = '', page = operatorCargoPage, perPage = operatorCargoPerPage) => {
    try {
      const params = { 
        page: page,
        per_page: perPage
      };
      
      if (filterStatus) {
        params.filter_status = filterStatus;
      }
      
      const response = await apiCall('/api/operator/cargo/list', 'GET', null, params);
      
      // Проверяем новый формат ответа с пагинацией
      if (response.items) {
        setOperatorCargo(response.items);
        setOperatorCargoPagination(response.pagination);
      } else {
        // Обратная совместимость со старым форматом
        setOperatorCargo(response.cargo_list || response);
        setOperatorCargoPagination({});
      }
    } catch (error) {
      console.error('Error fetching operator cargo:', error);
      setOperatorCargo([]);
      setOperatorCargoPagination({});
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
      setPendingOrders(data); // Также устанавливаем для нового функционала
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

  // НОВЫЕ ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ ЗАКАЗАМИ КЛИЕНТОВ

  const fetchNewOrdersCount = async () => {
    try {
      const data = await apiCall('/api/admin/new-orders-count');
      setNewOrdersCount(data.pending_orders);
    } catch (error) {
      console.error('Error fetching new orders count:', error);
    }
  };

  const fetchOrderDetails = async (orderId) => {
    try {
      const data = await apiCall(`/api/admin/cargo-requests/${orderId}`);
      setSelectedOrder(data);
      return data;
    } catch (error) {
      console.error('Error fetching order details:', error);
      return null;
    }
  };

  const handleOrderDetailsView = async (order) => {
    const details = await fetchOrderDetails(order.id);
    if (details) {
      setOrderDetailsModal(true);
    }
  };

  const handleOrderEdit = async (order) => {
    const details = await fetchOrderDetails(order.id);
    if (details) {
      // Заполнить форму редактирования данными заказа
      setOrderEditForm({
        sender_full_name: details.sender_full_name || '',
        sender_phone: details.sender_phone || '',
        recipient_full_name: details.recipient_full_name || '',
        recipient_phone: details.recipient_phone || '',
        recipient_address: details.recipient_address || '',
        pickup_address: details.pickup_address || '',
        cargo_name: details.cargo_name || '',
        weight: details.weight || '',
        declared_value: details.declared_value || '',
        description: details.description || '',
        route: details.route || '',
        admin_notes: details.admin_notes || ''
      });
      setEditOrderModal(true);
    }
  };

  const handleSaveOrderChanges = async () => {
    try {
      const updateData = { ...orderEditForm };
      
      // Преобразовать числовые поля
      if (updateData.weight) updateData.weight = parseFloat(updateData.weight);
      if (updateData.declared_value) updateData.declared_value = parseFloat(updateData.declared_value);

      await apiCall(`/api/admin/cargo-requests/${selectedOrder.id}/update`, 'PUT', updateData);
      
      showAlert('Заказ успешно обновлен!', 'success');
      setEditOrderModal(false);
      
      // Обновить данные
      fetchCargoRequests();
      fetchNewOrdersCount();
      
    } catch (error) {
      console.error('Error updating order:', error);
      showAlert('Ошибка обновления заказа: ' + (error.message || 'Неизвестная ошибка'), 'error');
    }
  };

  const handleAcceptOrder = async (orderId) => {
    try {
      await apiCall(`/api/admin/cargo-requests/${orderId}/accept`, 'POST');
      showAlert('Заказ принят и груз создан!', 'success');
      
      // Обновить данные
      fetchCargoRequests();
      fetchNewOrdersCount();
      fetchAllCargo();
      setOrderDetailsModal(false);
      
    } catch (error) {
      console.error('Error accepting order:', error);
      showAlert('Ошибка принятия заказа: ' + (error.message || 'Неизвестная ошибка'), 'error');
    }
  };

  const handleRejectOrder = async (orderId, reason = '') => {
    try {
      await apiCall(`/api/admin/cargo-requests/${orderId}/reject`, 'POST', { reason });
      showAlert('Заказ отклонен!', 'success');
      
      // Обновить данные
      fetchCargoRequests();
      fetchNewOrdersCount();
      setOrderDetailsModal(false);
      
    } catch (error) {
      console.error('Error rejecting order:', error);
      showAlert('Ошибка отклонения заказа: ' + (error.message || 'Неизвестная ошибка'), 'error');
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
      setShowSuggestions(false);
      return;
    }

    try {
      const results = await apiCall(`/api/cargo/search?query=${encodeURIComponent(query)}&search_type=${searchType}`);
      // Убеждаемся, что результат всегда является массивом
      setSearchResults(Array.isArray(results) ? results : []);
      setShowSearchResults(true);
      setShowSuggestions(false);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
      setShowSearchResults(false);
    }
  };

  // Advanced search function
  const handleAdvancedSearch = async (query = searchQuery, filters = searchFilters) => {
    setSearchLoading(true);
    try {
      const searchRequest = {
        query: query.trim(),
        search_type: searchType,
        ...filters
      };

      const response = await apiCall('/api/search/advanced', 'POST', searchRequest);
      
      setSearchResults(Array.isArray(response.results) ? response.results : []);
      setShowSearchResults(true);
      setShowSuggestions(false);
      setSearchTime(response.search_time_ms);
      
      // Обновляем предложения для автодополнения
      if (response.suggestions && response.suggestions.length > 0) {
        setSearchSuggestions(response.suggestions);
      }
      
    } catch (error) {
      console.error('Advanced search error:', error);
      setSearchResults([]);
      setShowSearchResults(false);
      setSearchTime(0);
    } finally {
      setSearchLoading(false);
    }
  };

  // Autocomplete suggestions
  const handleSearchInput = async (value) => {
    setSearchQuery(value);
    
    if (value.length >= 2) {
      try {
        // Используем простой поиск для получения предложений
        const response = await apiCall('/api/search/advanced', 'POST', {
          query: value.trim(),
          search_type: searchType,
          per_page: 5
        });
        
        if (response.suggestions && response.suggestions.length > 0) {
          setSearchSuggestions(response.suggestions);
          setShowSuggestions(true);
        } else {
          setShowSuggestions(false);
        }
      } catch (error) {
        setShowSuggestions(false);
      }
    } else {
      setShowSuggestions(false);
      setSearchSuggestions([]);
    }
  };

  const selectSearchSuggestion = (suggestion) => {
    setSearchQuery(suggestion);
    setShowSuggestions(false);
    handleAdvancedSearch(suggestion);
  };

  // Profile management functions
  const fetchOperatorProfile = async (operatorId) => {
    setProfileLoading(true);
    try {
      const profile = await apiCall(`/api/admin/operators/profile/${operatorId}`, 'GET');
      setSelectedOperatorProfile(profile);
      setShowOperatorProfile(true);
    } catch (error) {
      console.error('Error fetching operator profile:', error);
      showAlert('Ошибка загрузки профиля оператора', 'error');
    } finally {
      setProfileLoading(false);
    }
  };

  const fetchUserProfile = async (userId) => {
    setProfileLoading(true);
    try {
      const profile = await apiCall(`/api/admin/users/profile/${userId}`, 'GET');
      setSelectedUserProfile(profile);
      setFrequentRecipients(profile.frequent_recipients || []);
      setShowUserProfile(true);
    } catch (error) {
      console.error('Error fetching user profile:', error);
      showAlert('Ошибка загрузки профиля пользователя', 'error');
    } finally {
      setProfileLoading(false);
    }
  };

  // Quick cargo creation functions
  const openQuickCargoModal = (user) => {
    setQuickCargoForm({
      sender_id: user.id,
      recipient_data: {},
      cargo_items: [{ cargo_name: '', weight: '', price_per_kg: '' }],
      route: 'moscow_to_tajikistan',
      description: ''
    });
    
    // Загружаем профиль пользователя для получения частых получателей
    fetchUserProfile(user.id);
    setShowQuickCargoModal(true);
  };

  const selectRecipientFromHistory = (recipient) => {
    setSelectedRecipient(recipient);
    setQuickCargoForm({
      ...quickCargoForm,
      recipient_data: {
        recipient_full_name: recipient.recipient_full_name,
        recipient_phone: recipient.recipient_phone,
        recipient_address: recipient.recipient_address
      }
    });
  };

  const addQuickCargoItem = () => {
    setQuickCargoForm({
      ...quickCargoForm,
      cargo_items: [...quickCargoForm.cargo_items, { cargo_name: '', weight: '', price_per_kg: '' }]
    });
  };

  const removeQuickCargoItem = (index) => {
    if (quickCargoForm.cargo_items.length > 1) {
      const newItems = quickCargoForm.cargo_items.filter((_, i) => i !== index);
      setQuickCargoForm({
        ...quickCargoForm,
        cargo_items: newItems
      });
    }
  };

  const updateQuickCargoItem = (index, field, value) => {
    const newItems = [...quickCargoForm.cargo_items];
    newItems[index] = { ...newItems[index], [field]: value };
    setQuickCargoForm({
      ...quickCargoForm,
      cargo_items: newItems
    });
  };

  const calculateQuickCargoTotals = () => {
    const totalWeight = quickCargoForm.cargo_items.reduce((sum, item) => {
      return sum + (parseFloat(item.weight) || 0);
    }, 0);

    const totalCost = quickCargoForm.cargo_items.reduce((sum, item) => {
      const weight = parseFloat(item.weight) || 0;
      const price = parseFloat(item.price_per_kg) || 0;
      return sum + (weight * price);
    }, 0);

    return { totalWeight, totalCost };
  };

  const submitQuickCargo = async () => {
    try {
      const response = await apiCall(`/api/admin/users/${quickCargoForm.sender_id}/quick-cargo`, 'POST', quickCargoForm);
      showAlert('Груз успешно создан из профиля пользователя!', 'success');
      setShowQuickCargoModal(false);
      setShowUserProfile(false);
      
      // Обновляем список грузов
      fetchOperatorCargo();
      
    } catch (error) {
      console.error('Error creating quick cargo:', error);
      showAlert(error.message || 'Ошибка создания груза', 'error');
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
            <div class="logo" style="text-align: center; margin-bottom: 10px;">
              <img src="/logo.png" alt="TAJLINE.TJ" style="height: 60px; width: auto; margin: 0 auto;" onerror="this.style.display='none'; this.nextSibling.style.display='block';" />
              <div style="display: none; font-size: 24px; font-weight: bold; color: #2563eb;">📦 TAJLINE.TJ</div>
            </div>
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
            <p>Этот документ сформирован автоматически системой 
              <img src="/logo.png" alt="TAJLINE.TJ" style="height: 16px; width: auto; vertical-align: middle; margin: 0 5px;" onerror="this.style.display='none'; this.nextSibling.style.display='inline';" />
              <span style="display: none; font-weight: bold;">TAJLINE.TJ</span>
            </p>
            <p>Дата и время: ${new Date().toLocaleDateString('ru-RU')} ${new Date().toLocaleTimeString('ru-RU')}</p>
          </div>
        </body>
      </html>
    `);
    
    printWindow.document.close();
    printWindow.print();
  };

  // Print invoice for individual cargo - TAJLINE format
  const printInvoice = (cargo) => {
    // Попытка открыть новое окно
    const printWindow = window.open('', '_blank');
    
    // Проверяем, удалось ли открыть окно (может быть заблокировано браузером)
    if (!printWindow) {
      // Если окно не открылось, используем альтернативный метод
      showAlert('Всплывающие окна заблокированы. Накладная будет открыта в новой вкладке.', 'warning');
      
      // Создаем временный элемент для печати
      const printContent = createInvoiceHTML(cargo);
      
      // Открываем в новой вкладке с data URL
      const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(printContent)}`;
      window.open(dataUrl, '_blank');
      return;
    }
    
    try {
      const invoiceHTML = createInvoiceHTML(cargo);
      printWindow.document.write(invoiceHTML);
      printWindow.document.close();
    } catch (error) {
      console.error('Error creating print window:', error);
      showAlert('Ошибка создания накладной. Попробуйте снова.', 'error');
      if (printWindow) {
        printWindow.close();
      }
    }
  };

  // Функция создания HTML для накладной
  const createInvoiceHTML = (cargo) => {
    // Получаем текущую дату в формате dd.mm.yy
    const currentDate = new Date().toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit'
    });
    
    // Определяем пункт назначения по маршруту
    const getDestination = (route) => {
      switch(route) {
        case 'moscow_dushanbe': return 'Душанбе';
        case 'moscow_khujand': return 'Худжанд';
        case 'moscow_kulob': return 'Кулоб';
        case 'moscow_kurgantyube': return 'Курган-Тюбе';
        default: return 'Таджикистан';
      }
    };
    
    // Подготавливаем данные груза для таблицы
    let cargoItems = [];
    if (cargo.cargo_items && Array.isArray(cargo.cargo_items)) {
      // Мульти-груз
      cargoItems = cargo.cargo_items.map(item => ({
        name: item.cargo_name || 'Товар',
        quantity: item.weight || 0,
        unit: 'кг',
        price: item.price_per_kg || 0,
        total: (item.weight || 0) * (item.price_per_kg || 0)
      }));
    } else {
      // Одиночный груз
      cargoItems = [{
        name: cargo.cargo_name || cargo.description || 'Товар',
        quantity: cargo.weight || 0,
        unit: 'кг', 
        price: cargo.price_per_kg || (cargo.total_cost || 0) / (cargo.weight || 1),
        total: cargo.total_cost || cargo.declared_value || 0
      }];
    }
    
    const totalWeight = cargoItems.reduce((sum, item) => sum + item.quantity, 0);
    const totalAmount = cargoItems.reduce((sum, item) => sum + item.total, 0);
    
    return `
      <html>
        <head>
          <title>Накладная TAJLINE № ${cargo.cargo_number}</title>
          <meta charset="utf-8">
          <style>
            @page {
              size: A4;
              margin: 15mm;
            }
            
            body {
              font-family: Arial, sans-serif;
              margin: 0;
              padding: 0;
              font-size: 11px;
              line-height: 1.2;
              color: #000;
            }
            
            .invoice-container {
              max-width: 100%;
              margin: 0 auto;
            }
            
            .header {
              text-align: center;
              margin-bottom: 20px;
              border-bottom: 2px solid #000;
              padding-bottom: 15px;
            }
            
            .logo {
              font-size: 24px;
              font-weight: bold;
              letter-spacing: 2px;
              margin-bottom: 10px;
              color: #000;
            }
            
            .contacts {
              font-size: 9px;
              line-height: 1.3;
              color: #666;
              margin-bottom: 15px;
            }
            
            .invoice-number {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 15px;
            }
            
            .invoice-number .label {
              font-weight: bold;
              font-size: 12px;
            }
            
            .invoice-number .number-box,
            .invoice-number .date-box {
              border: 2px solid #000;
              padding: 8px 15px;
              font-weight: bold;
              font-size: 14px;
              min-width: 120px;
              text-align: center;
            }
            
            .info-row {
              display: flex;
              margin-bottom: 5px;
              border: 1px solid #000;
            }
            
            .info-cell {
              padding: 6px 8px;
              border-right: 1px solid #000;
              font-size: 10px;
            }
            
            .info-cell:last-child {
              border-right: none;
            }
            
            .info-cell.label {
              background-color: #f5f5f5;
              font-weight: bold;
              width: 15%;
              text-align: center;
            }
            
            .info-cell.wide {
              width: 35%;
            }
            
            .cargo-table {
              width: 100%;
              border-collapse: collapse;
              margin: 15px 0;
              border: 2px solid #000;
            }
            
            .cargo-table th,
            .cargo-table td {
              border: 1px solid #000;
              padding: 6px;
              text-align: center;
              font-size: 10px;
            }
            
            .cargo-table th {
              background-color: #f5f5f5;
              font-weight: bold;
            }
            
            .cargo-table .item-name {
              text-align: left;
            }
            
            .total-row {
              font-weight: bold;
              background-color: #f9f9f9;
            }
            
            .cargo-value {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin: 15px 0;
              font-weight: bold;
              font-size: 12px;
            }
            
            .signatures {
              margin-top: 30px;
              display: flex;
              justify-content: space-between;
            }
            
            .signature-block {
              width: 30%;
              text-align: center;
              border-bottom: 1px solid #000;
              padding-bottom: 2px;
              margin-bottom: 5px;
            }
            
            .signature-label {
              font-size: 9px;
              margin-top: 5px;
            }
            
            .terms {
              font-size: 8px;
              line-height: 1.3;
              margin-top: 20px;
              border-top: 1px solid #ccc;
              padding-top: 10px;
            }
            
            .terms p {
              margin: 5px 0;
              text-align: justify;
            }
            
            @media print {
              body { -webkit-print-color-adjust: exact; }
              .no-print { display: none !important; }
            }
          </style>
        </head>
        <body>
          <div class="invoice-container">
            <!-- Header -->
            <div class="header">
              <div class="logo">TAJLINE</div>
              <div class="contacts">
                <strong>Наши контакты</strong><br>
                МСК: (968) 658-8858<br>
                МСК: (977) 904-8888<br>
                Склад в Худжанде: +992 92 650 5001<br>
                Склад в Худжанде: +992 92 913 2442<br>
                Склад в Душанбе: +992 91 868 3313
              </div>
            </div>
            
            <!-- Invoice Number and Date -->
            <div class="invoice-number">
              <span class="label">Накладная №</span>
              <div class="number-box">${cargo.cargo_number || 'N/A'}</div>
              <span class="label">от</span>
              <div class="date-box">${currentDate}</div>
            </div>
            
            <!-- Destination -->
            <div class="info-row">
              <div class="info-cell label">Пункт назначения</div>
              <div class="info-cell" style="flex: 1; text-align: center; font-weight: bold;">
                ${getDestination(cargo.route)}
              </div>
            </div>
            
            <!-- Sender and Recipient -->
            <div class="info-row">
              <div class="info-cell label">Отправитель</div>
              <div class="info-cell wide">${cargo.sender_full_name || 'Не указан'}</div>
              <div class="info-cell label">Получатель</div>
              <div class="info-cell wide">${cargo.recipient_full_name || cargo.recipient_name || 'Не указан'}</div>
            </div>
            
            <div class="info-row">
              <div class="info-cell label">Телефон</div>
              <div class="info-cell wide">${cargo.sender_phone || 'Не указан'}</div>
              <div class="info-cell label">Телефон</div>
              <div class="info-cell wide">${cargo.recipient_phone || 'Не указан'}</div>
            </div>
            
            <!-- Cargo Table -->
            <table class="cargo-table">
              <thead>
                <tr>
                  <th style="width: 5%;">№</th>
                  <th style="width: 35%;">Наименование товара</th>
                  <th style="width: 15%;">Кол-во</th>
                  <th style="width: 10%;">Ед.</th>
                  <th style="width: 15%;">Цена за кг</th>
                  <th style="width: 20%;">Сумма</th>
                </tr>
              </thead>
              <tbody>
                ${cargoItems.map((item, index) => `
                  <tr>
                    <td>${index + 1}</td>
                    <td class="item-name">${item.name}</td>
                    <td>${item.quantity}</td>
                    <td>${item.unit}</td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>${item.total.toFixed(2)}</td>
                  </tr>
                `).join('')}
                <tr class="total-row">
                  <td colspan="2"><strong>Итого:</strong></td>
                  <td><strong>${totalWeight}</strong></td>
                  <td><strong>кг</strong></td>
                  <td></td>
                  <td><strong>${totalAmount.toFixed(2)} ₽</strong></td>
                </tr>
              </tbody>
            </table>
            
            <!-- Volume -->
            <div style="text-align: right; margin: 10px 0;">
              <span style="border: 1px solid #000; padding: 5px 10px;">
                куб.м
              </span>
            </div>
            
            <!-- Signatures -->
            <div class="signatures">
              <div>
                <div class="signature-block"></div>
                <div class="signature-label">м.п.</div>
              </div>
              <div>
                <div class="signature-block"></div>
                <div class="signature-label"></div>
              </div>
              <div>
                <div class="signature-block">подпись</div>
                <div class="signature-label"></div>
              </div>
            </div>
            
            <!-- Cargo Value -->
            <div class="cargo-value">
              <span>Ценность груза:</span>
              <span>${cargo.declared_value || totalAmount.toFixed(0)} руб.</span>
            </div>
            
            <!-- Terms -->
            <div class="terms">
              <p><strong>Условия перевозки</strong></p>
              <p>1. Срок хранения товара Исполнителем в Пункте назначения составляет 5 рабочих дней с момента отправки уведомления об успешной доставке в Пункт назначения. При несвоевременном получении товара Заказчиком возникает обязанность Заказчика уплатить дополнительные пени в размере 0,1% за каждый день превышения Срока хранения товара в Пункте назначения</p>
              <p>2. При возникновении обстоятельств непреодолимой силы (таких как: пожары, наводнения, землетрясения, военные действия и пр.) и невозможности сохранения товаров Заказчика, Исполнитель обязуется вернуть Заказчику денежные средства в размере, трёхкратно превышающем сумму, оплаченную Заказчиком за доставку товара по Накладной № ${cargo.cargo_number || 'N/A'}.</p>
            </div>
          </div>
          
          <script>
            window.onload = function() {
              setTimeout(function() {
                window.print();
                window.onafterprint = function() {
                  window.close();
                };
              }, 500);
            };
          </script>
        </body>
      </html>
    `;
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
              <div style="text-align: center; margin-bottom: 15px;">
                <img src="/logo.png" alt="TAJLINE.TJ" style="height: 40px; width: auto;" onerror="this.style.display='none'; this.nextSibling.style.display='block';" />
                <div style="display: none; font-weight: bold; color: #2563eb; font-size: 18px;">TAJLINE.TJ</div>
              </div>
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
    setIsLoggingIn(true);
    try {
      const data = await apiCall('/api/auth/login', 'POST', loginForm);
      
      // Устанавливаем токен и пользователя одновременно
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      
      showAlert('Успешный вход в систему!', 'success');
      
      // Сбрасываем флаг логина после небольшой задержки
      setTimeout(() => {
        setIsLoggingIn(false);
      }, 1000);
      
    } catch (error) {
      console.error('Login error:', error);
      setIsLoggingIn(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoggingIn(true);
    try {
      const data = await apiCall('/api/auth/register', 'POST', registerForm);
      
      // Устанавливаем токен и пользователя одновременно
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('token', data.access_token);
      
      showAlert('Регистрация прошла успешно!', 'success');
      
      // Сбрасываем флаг логина после небольшой задержки
      setTimeout(() => {
        setIsLoggingIn(false);
      }, 1000);
      
    } catch (error) {
      console.error('Registration error:', error);
      setIsLoggingIn(false);
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
      // Убеждаемся, что результат всегда является массивом
      setSearchResults(Array.isArray(data) ? data : []);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
      setShowSearchResults(false);
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

  // Функции для управления множественными грузами с индивидуальными ценами
  const addCargoItem = () => {
    setOperatorCargoForm({
      ...operatorCargoForm,
      cargo_items: [...operatorCargoForm.cargo_items, { cargo_name: '', weight: '', price_per_kg: '' }]
    });
  };

  const removeCargoItem = (index) => {
    if (operatorCargoForm.cargo_items.length > 1) {
      const newItems = operatorCargoForm.cargo_items.filter((_, i) => i !== index);
      setOperatorCargoForm({
        ...operatorCargoForm,
        cargo_items: newItems
      });
      calculateTotalsWithIndividualPrices(newItems);
    }
  };

  const updateCargoItem = (index, field, value) => {
    const newItems = [...operatorCargoForm.cargo_items];
    newItems[index] = { ...newItems[index], [field]: value };
    setOperatorCargoForm({
      ...operatorCargoForm,
      cargo_items: newItems
    });
    calculateTotalsWithIndividualPrices(newItems);
  };

  const calculateTotalsWithIndividualPrices = (cargoItems = operatorCargoForm.cargo_items) => {
    let totalWeightSum = 0;
    let totalCostSum = 0;
    const breakdown = [];
    
    cargoItems.forEach((item, index) => {
      const weight = parseFloat(item.weight) || 0;
      const pricePerKg = parseFloat(item.price_per_kg) || 0;
      const itemCost = weight * pricePerKg;
      
      totalWeightSum += weight;
      totalCostSum += itemCost;
      
      if (weight > 0 && pricePerKg > 0) {
        breakdown.push({
          index: index + 1,
          name: item.cargo_name || `Груз ${index + 1}`,
          weight,
          pricePerKg,
          cost: itemCost
        });
      }
    });
    
    setTotalWeight(totalWeightSum);
    setTotalCost(totalCostSum);
    setCargoBreakdown(breakdown);
  };

  // Старая функция calculateTotals для совместимости с режимом общей цены
  const calculateTotals = (cargoItems = operatorCargoForm.cargo_items, pricePerKg = operatorCargoForm.price_per_kg) => {
    const weight = cargoItems.reduce((sum, item) => {
      const itemWeight = parseFloat(item.weight) || 0;
      return sum + itemWeight;
    }, 0);
    
    const cost = weight * (parseFloat(pricePerKg) || 0);
    
    setTotalWeight(weight);
    setTotalCost(cost);
  };

  const handleAcceptCargo = async (e) => {
    e.preventDefault();
    try {
      let requestData;
      
      if (operatorCargoForm.use_multi_cargo) {
        // Новый режим с множественными грузами и индивидуальными ценами
        requestData = {
          sender_full_name: operatorCargoForm.sender_full_name,
          sender_phone: operatorCargoForm.sender_phone,
          recipient_full_name: operatorCargoForm.recipient_full_name,
          recipient_phone: operatorCargoForm.recipient_phone,
          recipient_address: operatorCargoForm.recipient_address,
          description: operatorCargoForm.description,
          route: operatorCargoForm.route,
          cargo_items: operatorCargoForm.cargo_items.map(item => ({
            cargo_name: item.cargo_name,
            weight: parseFloat(item.weight),
            price_per_kg: parseFloat(item.price_per_kg)
          }))
        };
      } else {
        // Старый режим для совместимости
        requestData = {
          ...operatorCargoForm,
          weight: parseFloat(operatorCargoForm.weight),
          declared_value: parseFloat(operatorCargoForm.declared_value || operatorCargoForm.price_per_kg),
          price_per_kg: parseFloat(operatorCargoForm.declared_value || operatorCargoForm.price_per_kg)
        };
      }
      
      await apiCall('/api/operator/cargo/accept', 'POST', requestData);
      showAlert('Груз успешно принят!', 'success');
      
      // Сброс формы
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
        route: 'moscow_to_tajikistan',
        cargo_items: [{ cargo_name: '', weight: '', price_per_kg: '' }],
        price_per_kg: '',
        use_multi_cargo: false
      });
      
      // Сброс калькулятора
      setTotalWeight(0);
      setTotalCost(0);
      setCargoBreakdown([]);
      
      // Сброс флагов автозаполнения
      setIsFilledFromProfile(false);
      setProfileSourceUser(null);
      
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
    console.log('Opening warehouse layout for:', warehouse);
    setSelectedWarehouseForLayout(warehouse);
    
    // Используем новый API для получения схемы с информацией о грузах
    try {
      await fetchWarehouseLayoutWithCargo(warehouse.id);
      console.log('Layout fetched, opening modal...');
      setLayoutModal(true);
    } catch (error) {
      console.error('Error opening warehouse layout:', error);
      showAlert('Ошибка при открытии схемы склада: ' + error.message, 'error');
    }
  };

  const printCargoInvoice = (cargo) => {
    // Используем тот же формат, что и printInvoice
    printInvoice(cargo);
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
        declared_value: getDefaultDeclaredValue('moscow_to_tajikistan'), // Используем значение по умолчанию
        description: '',
        route: 'moscow_to_tajikistan'
      });
      fetchMyRequests();
    } catch (error) {
      console.error('Create request error:', error);
      
      // Правильная обработка ошибок
      let errorMessage = 'Неизвестная ошибка при подаче заявки';
      
      if (error.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error.detail) {
        errorMessage = error.detail;
      }
      
      showAlert('Ошибка подачи заявки: ' + errorMessage, 'error');
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

  // Функция для проверки валидности токена
  const isTokenValid = (tokenString) => {
    if (!tokenString) return false;
    
    try {
      // Декодируем JWT токен без проверки подписи (только для получения exp)
      const base64Url = tokenString.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      
      const decoded = JSON.parse(jsonPayload);
      const currentTime = Date.now() / 1000;
      
      // Проверяем, не истек ли токен
      return decoded.exp && decoded.exp > currentTime;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  };

  const handleLogout = () => {
    // Предотвращаем множественные logout'ы
    if (isLoggingOut) {
      console.log('Logout already in progress, skipping...');
      return;
    }
    
    console.log('Starting logout process...');
    setIsLoggingOut(true);
    
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
    
    // Перенаправляем на страницу входа
    setActiveTab('login');
    setActiveSection('login');
    
    showAlert('Вы вышли из системы', 'info');
    
    // Сбрасываем флаг логаута через небольшую задержку
    setTimeout(() => {
      setIsLoggingOut(false);
      console.log('Logout process completed');
    }, 1000);
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

  // Функция для редактирования профиля пользователя
  const openEditProfile = () => {
    setEditProfileForm({
      full_name: user.full_name || '',
      phone: user.phone || '',
      email: user.email || '',
      address: user.address || ''
    });
    setShowEditProfile(true);
  };

  const saveProfile = async () => {
    try {
      const updatedUser = await apiCall('/api/user/profile', 'PUT', editProfileForm);
      setUser(updatedUser);
      setShowEditProfile(false);
      showAlert('Профиль обновлен успешно!', 'success');
    } catch (error) {
      showAlert('Ошибка обновления профиля: ' + error.message, 'error');
    }
  };

  // Функция для открытия модального окна повторного заказа
  const openRepeatOrder = (cargo) => {
    setRepeatOrderData(cargo);
    setRepeatOrderForm({
      cargo_items: [{ 
        cargo_name: cargo.cargo_name || cargo.description || 'Груз', 
        weight: cargo.weight || '', 
        price_per_kg: cargo.price_per_kg || '50' 
      }],
      recipient_full_name: cargo.recipient_full_name || '',
      recipient_phone: cargo.recipient_phone || '',
      recipient_address: cargo.recipient_address || '',
      route: cargo.route || 'moscow_dushanbe',
      delivery_type: 'standard',
      insurance_requested: false,
      special_instructions: '',
      use_multi_cargo: true
    });
    setShowRepeatOrderModal(true);
    calculateRepeatOrderTotals([{ 
      cargo_name: cargo.cargo_name || cargo.description || 'Груз', 
      weight: cargo.weight || '', 
      price_per_kg: cargo.price_per_kg || '50' 
    }]);
  };

  // Функция для расчета итогов повторного заказа
  const calculateRepeatOrderTotals = (cargoItems) => {
    let totalWeight = 0;
    let totalCost = 0;
    const breakdown = [];

    cargoItems.forEach((item, index) => {
      const weight = parseFloat(item.weight) || 0;
      const pricePerKg = parseFloat(item.price_per_kg) || 0;
      const itemCost = weight * pricePerKg;

      totalWeight += weight;
      totalCost += itemCost;

      breakdown.push({
        index: index,
        cargo_name: item.cargo_name || `Груз ${index + 1}`,
        weight: weight,
        price_per_kg: pricePerKg,
        cost: itemCost
      });
    });

    setRepeatOrderTotalWeight(totalWeight);
    setRepeatOrderTotalCost(totalCost);
    setRepeatOrderBreakdown(breakdown);
  };

  // Обработчик изменения элементов груза в повторном заказе
  const handleRepeatOrderItemChange = (index, field, value) => {
    const updatedItems = [...repeatOrderForm.cargo_items];
    updatedItems[index] = { ...updatedItems[index], [field]: value };
    setRepeatOrderForm({ ...repeatOrderForm, cargo_items: updatedItems });
    calculateRepeatOrderTotals(updatedItems);
  };

  // Добавление нового элемента груза в повторный заказ
  const addRepeatOrderItem = () => {
    const newItems = [...repeatOrderForm.cargo_items, { cargo_name: '', weight: '', price_per_kg: '50' }];
    setRepeatOrderForm({ ...repeatOrderForm, cargo_items: newItems });
    calculateRepeatOrderTotals(newItems);
  };

  // Удаление элемента груза из повторного заказа
  const removeRepeatOrderItem = (index) => {
    if (repeatOrderForm.cargo_items.length > 1) {
      const newItems = repeatOrderForm.cargo_items.filter((_, i) => i !== index);
      setRepeatOrderForm({ ...repeatOrderForm, cargo_items: newItems });
      calculateRepeatOrderTotals(newItems);
    }
  };

  // Отправка повторного заказа
  const submitRepeatOrder = async () => {
    try {
      if (repeatOrderForm.cargo_items.some(item => !item.cargo_name || !item.weight || !item.price_per_kg)) {
        showAlert('Пожалуйста, заполните все поля для всех грузов', 'error');
        return;
      }

      if (!repeatOrderForm.recipient_full_name || !repeatOrderForm.recipient_phone) {
        showAlert('Пожалуйста, заполните данные получателя', 'error');
        return;
      }

      const orderData = {
        ...repeatOrderForm,
        sender_full_name: user.full_name,
        sender_phone: user.phone,
        total_weight: repeatOrderTotalWeight,
        total_cost: repeatOrderTotalCost
      };

      const result = await apiCall('/api/operator/cargo/accept', 'POST', orderData);
      
      setShowRepeatOrderModal(false);
      setRepeatOrderData(null);
      
      // Обновляем данные клиента
      fetchClientDashboard();
      fetchClientCargo();
      
      showAlert(`Повторный заказ успешно создан! Номер: ${result.cargo_number}`, 'success');
      
    } catch (error) {
      console.error('Error creating repeat order:', error);
      showAlert('Ошибка создания заказа: ' + error.message, 'error');
    }
  };

  // Функции для редактирования пользователей админом
  const openAdminEditUser = (user) => {
    setSelectedUserForEdit(user);
    setAdminEditUserForm({
      id: user.id,
      full_name: user.full_name || '',
      phone: user.phone || '',
      email: user.email || '',
      address: user.address || '',
      role: user.role || 'user',
      is_active: user.is_active !== undefined ? user.is_active : true
    });
    setShowAdminEditUser(true);
  };

  const saveAdminUserEdit = async () => {
    try {
      const updatedUser = await apiCall(`/api/admin/users/${adminEditUserForm.id}/update`, 'PUT', adminEditUserForm);
      setShowAdminEditUser(false);
      setSelectedUserForEdit(null);
      
      // Обновляем списки пользователей
      fetchUsers();
      fetchUsersByRole();
      
      showAlert('Данные пользователя обновлены успешно!', 'success');
    } catch (error) {
      showAlert('Ошибка обновления данных пользователя: ' + error.message, 'error');
    }
  };

  // Функции для повторного заказа админом/оператором
  const openAdminRepeatOrder = (cargo) => {
    setAdminRepeatOrderData(cargo);
    setAdminRepeatOrderForm({
      sender_id: cargo.sender_id || '',
      sender_full_name: cargo.sender_full_name || '',
      sender_phone: cargo.sender_phone || '',
      cargo_items: [{ 
        cargo_name: '', // Админ должен заполнить заново
        weight: '', // Админ должен заполнить заново
        price_per_kg: '50' // Значение по умолчанию
      }],
      recipient_full_name: cargo.recipient_full_name || '',
      recipient_phone: cargo.recipient_phone || '',
      recipient_address: cargo.recipient_address || '',
      route: cargo.route || 'moscow_dushanbe',
      delivery_type: 'standard',
      insurance_requested: false,
      special_instructions: `Повтор груза №${cargo.cargo_number}`,
      use_multi_cargo: true
    });
    setShowAdminRepeatOrderModal(true);
    calculateAdminRepeatOrderTotals([{ 
      cargo_name: '', 
      weight: '', 
      price_per_kg: '50'
    }]);
  };

  // Функция для расчета итогов повторного заказа админа/оператора
  const calculateAdminRepeatOrderTotals = (cargoItems) => {
    let totalWeight = 0;
    let totalCost = 0;
    const breakdown = [];

    cargoItems.forEach((item, index) => {
      const weight = parseFloat(item.weight) || 0;
      const pricePerKg = parseFloat(item.price_per_kg) || 0;
      const itemCost = weight * pricePerKg;

      totalWeight += weight;
      totalCost += itemCost;

      breakdown.push({
        index: index,
        cargo_name: item.cargo_name || `Груз ${index + 1}`,
        weight: weight,
        price_per_kg: pricePerKg,
        cost: itemCost
      });
    });

    setAdminRepeatOrderTotalWeight(totalWeight);
    setAdminRepeatOrderTotalCost(totalCost);
    setAdminRepeatOrderBreakdown(breakdown);
  };

  // Обработчик изменения элементов груза в повторном заказе админа
  const handleAdminRepeatOrderItemChange = (index, field, value) => {
    const updatedItems = [...adminRepeatOrderForm.cargo_items];
    updatedItems[index] = { ...updatedItems[index], [field]: value };
    setAdminRepeatOrderForm({ ...adminRepeatOrderForm, cargo_items: updatedItems });
    calculateAdminRepeatOrderTotals(updatedItems);
  };

  // Добавление нового элемента груза в повторный заказ админа
  const addAdminRepeatOrderItem = () => {
    const newItems = [...adminRepeatOrderForm.cargo_items, { cargo_name: '', weight: '', price_per_kg: '50' }];
    setAdminRepeatOrderForm({ ...adminRepeatOrderForm, cargo_items: newItems });
    calculateAdminRepeatOrderTotals(newItems);
  };

  // Удаление элемента груза из повторного заказа админа
  const removeAdminRepeatOrderItem = (index) => {
    if (adminRepeatOrderForm.cargo_items.length > 1) {
      const newItems = adminRepeatOrderForm.cargo_items.filter((_, i) => i !== index);
      setAdminRepeatOrderForm({ ...adminRepeatOrderForm, cargo_items: newItems });
      calculateAdminRepeatOrderTotals(newItems);
    }
  };

  // Отправка повторного заказа админом/оператором
  const submitAdminRepeatOrder = async () => {
    try {
      if (adminRepeatOrderForm.cargo_items.some(item => !item.cargo_name || !item.weight || !item.price_per_kg)) {
        showAlert('Пожалуйста, заполните все поля для всех грузов', 'error');
        return;
      }

      if (!adminRepeatOrderForm.recipient_full_name || !adminRepeatOrderForm.recipient_phone) {
        showAlert('Пожалуйста, заполните данные получателя', 'error');
        return;
      }

      if (!adminRepeatOrderForm.sender_full_name || !adminRepeatOrderForm.sender_phone) {
        showAlert('Пожалуйста, заполните данные отправителя', 'error');
        return;
      }

      const orderData = {
        ...adminRepeatOrderForm,
        total_weight: adminRepeatOrderTotalWeight,
        total_cost: adminRepeatOrderTotalCost
      };

      const result = await apiCall('/api/operator/cargo/accept', 'POST', orderData);
      
      setShowAdminRepeatOrderModal(false);
      setAdminRepeatOrderData(null);
      
      // Обновляем данные
      if (user.role === 'admin') {
        fetchAllCargo();
      } else if (user.role === 'warehouse_operator') {
        fetchOperatorCargo();
      }
      
      showAlert(`Повторный заказ успешно создан! Номер: ${result.cargo_number}`, 'success');
      
    } catch (error) {
      console.error('Error creating admin repeat order:', error);
      showAlert('Ошибка создания заказа: ' + error.message, 'error');
    }
  };

  // Функция для открытия формы приема груза из профиля пользователя
  const openQuickCargoFromProfile = async (userInfo) => {
    try {
      // Закрываем модальное окно профиля
      setShowUserProfile(false);
      
      // Получаем историю отправлений пользователя для автозаполнения
      const historyData = selectedUserProfile?.sent_cargo || [];
      
      let senderData = {
        full_name: userInfo.full_name || '',
        phone: userInfo.phone || '',
        address: userInfo.address || ''
      };
      
      let recipientData = {
        full_name: '',
        phone: '',
        address: ''
      };
      
      // Если есть история отправлений, берем данные последнего отправления
      if (historyData.length > 0) {
        const lastCargo = historyData[0]; // Первый элемент - самый последний
        recipientData = {
          full_name: lastCargo.recipient_full_name || lastCargo.recipient_name || '',
          phone: lastCargo.recipient_phone || '',
          address: lastCargo.recipient_address || ''
        };
      }
      
      // Заполняем форму оператора с автозаполненными данными
      const formData = {
        sender_full_name: senderData.full_name,
        sender_phone: senderData.phone,
        sender_address: senderData.address,
        recipient_full_name: recipientData.full_name,
        recipient_phone: recipientData.phone,
        recipient_address: recipientData.address,
        cargo_items: [{ cargo_name: '', weight: '', price_per_kg: '50' }],
        route: historyData.length > 0 ? historyData[0].route || 'moscow_dushanbe' : 'moscow_dushanbe',
        delivery_type: 'standard',
        insurance_requested: false,
        special_instructions: `Груз для ${userInfo.full_name} (${userInfo.user_number})`,
        use_multi_cargo: true
      };
      
      setOperatorCargoForm(formData);
      
      // Устанавливаем флаг автозаполнения
      setIsFilledFromProfile(true);
      setProfileSourceUser(userInfo);
      
      // Рассчитываем калькулятор
      calculateTotalsWithIndividualPrices([{ cargo_name: '', weight: '', price_per_kg: '50' }]);
      
      // Переходим на страницу приема груза
      setActiveSection('cargo-management');
      setActiveTab('cargo-accept');
      
      if (historyData.length > 0) {
        showAlert(`Форма заполнена данными пользователя: ${userInfo.full_name}. Данные получателя взяты из последней отправки.`, 'info');
      } else {
        showAlert(`Форма заполнена данными пользователя: ${userInfo.full_name}. Данные получателя нужно заполнить вручную.`, 'warning');
      }
      
    } catch (error) {
      console.error('Error opening cargo form from profile:', error);
      showAlert('Ошибка открытия формы: ' + error.message, 'error');
    }
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
        id: 'personal-dashboard',
        label: 'Личный кабинет',
        icon: <User className="w-5 h-5" />,
        section: 'personal-dashboard'
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
          { id: 'users-create-operator', label: 'Создать оператора' }, // Функция 2
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
          { id: 'notifications-client-orders', label: `Новые заказы (${newOrdersCount})` },
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
                <img 
                  src="/logo.png" 
                  alt="TAJLINE.TJ" 
                  className="h-16 w-auto"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'block';
                  }}
                />
                <div className="hidden">
                  <div className="bg-blue-600 text-white p-2 rounded-lg">
                    <Truck className="h-12 w-12" />
                  </div>
                  <h1 className="text-3xl font-bold text-blue-600 mt-2">TAJLINE.TJ</h1>
                </div>
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
                  <img 
                    src="/logo.png" 
                    alt="TAJLINE.TJ" 
                    className="h-10 w-auto"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'block';
                    }}
                  />
                  <div className="hidden flex items-center">
                    <div className="bg-blue-600 text-white p-2 rounded-lg mr-3">
                      <Truck className="h-8 w-8" />
                    </div>
                    <div>
                      <h1 className="text-2xl font-bold text-blue-600">TAJLINE.TJ</h1>
                      <p className="text-sm text-gray-600">Грузоперевозки Москва-Таджикистан</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  {getRoleIcon(user.role)}
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{user.full_name}</span>
                    {user.user_number && (
                      <span className="text-xs text-gray-500">№ {user.user_number}</span>
                    )}
                  </div>
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
          {/* Новая главная страница для клиентов с личным кабинетом (Функция 1) */}
          {user?.role === 'user' ? (
            <div className="space-y-6">
              {/* Client Dashboard Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <img 
                    src="/logo.png" 
                    alt="TAJLINE.TJ" 
                    className="h-12 w-auto"
                    onError={(e) => {
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'block';
                    }}
                  />
                  <div className="hidden">
                    <h1 className="text-3xl font-bold text-gray-900">TAJLINE.TJ</h1>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">Добро пожаловать, {user.full_name}!</h1>
                    <p className="text-gray-600 mt-1">Ваш личный кабинет для управления грузами</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <Button 
                    variant="outline" 
                    onClick={openEditProfile}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    <Settings className="mr-2 h-4 w-4" />
                    Редактировать профиль
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      fetchClientDashboard();
                      fetchClientCargo();
                    }}
                  >
                    <Package className="mr-2 h-4 w-4" />
                    Обновить
                  </Button>
                </div>
              </div>

              {/* Client Dashboard Stats */}
              {clientDashboard && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <Package className="h-8 w-8 text-blue-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-600">Всего грузов</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {clientDashboard.cargo_summary?.total_cargo || 0}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <Clock className="h-8 w-8 text-yellow-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-600">В пути</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {clientDashboard.cargo_summary?.status_breakdown?.in_transit || 0}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <CheckCircle className="h-8 w-8 text-green-600" />
                        <div className="ml-4">  
                          <p className="text-sm font-medium text-gray-600">Доставлено</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {clientDashboard.cargo_summary?.status_breakdown?.delivered || 0}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center">
                        <CreditCard className="h-8 w-8 text-red-600" />
                        <div className="ml-4">
                          <p className="text-sm font-medium text-gray-600">К оплате</p>
                          <p className="text-2xl font-bold text-gray-900">
                            {clientDashboard.cargo_summary?.unpaid_cargo_count || 0}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Client Navigation Tabs */}
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="dashboard" className="flex items-center">
                    <Home className="mr-2 h-4 w-4" />
                    Главная
                  </TabsTrigger>
                  <TabsTrigger value="create-order" className="flex items-center">
                    <Plus className="mr-2 h-4 w-4" />
                    Оформить груз
                  </TabsTrigger>
                  <TabsTrigger value="cargo" className="flex items-center">
                    <Package className="mr-2 h-4 w-4" />
                    Мои грузы
                  </TabsTrigger>
                  <TabsTrigger value="requests" className="flex items-center">
                    <FileText className="mr-2 h-4 w-4" />
                    Заявки
                  </TabsTrigger>
                  <TabsTrigger value="contact" className="flex items-center">
                    <MessageCircle className="mr-2 h-4 w-4" />
                    Связь
                  </TabsTrigger>
                </TabsList>

                {/* Dashboard Tab */}
                <TabsContent value="dashboard" className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Recent Cargo */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Package className="mr-2 h-5 w-5" />
                          Последние грузы
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {clientDashboard?.recent_cargo && clientDashboard.recent_cargo.length > 0 ? (
                            clientDashboard.recent_cargo.slice(0, 3).map((cargo) => (
                              <div key={cargo.id} className="flex items-center justify-between p-3 border rounded-lg">
                                <div>
                                  <div className="font-medium">#{cargo.cargo_number}</div>
                                  <div className="text-sm text-gray-600">{cargo.cargo_name || 'Груз'}</div>
                                  <div className="text-xs text-gray-500">
                                    {cargo.recipient_full_name}
                                  </div>
                                </div>
                                <Badge variant={cargo.status === 'delivered' ? 'default' : 'outline'}>
                                  {cargo.status}
                                </Badge>
                              </div>
                            ))
                          ) : (
                            <p className="text-gray-500 text-center py-4">Нет последних грузов</p>
                          )}
                        </div>
                        <div className="mt-4">
                          <Button 
                            variant="outline" 
                            className="w-full" 
                            onClick={() => {
                              setActiveTab('cargo');
                              fetchClientCargo();
                            }}
                          >
                            Посмотреть все грузы
                          </Button>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Unpaid Cargo */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <CreditCard className="mr-2 h-5 w-5 text-red-600" />
                          К оплате
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {clientDashboard?.unpaid_cargo && clientDashboard.unpaid_cargo.length > 0 ? (
                            clientDashboard.unpaid_cargo.slice(0, 3).map((cargo) => (
                              <div key={cargo.id} className="flex items-center justify-between p-3 border rounded-lg bg-red-50">
                                <div>
                                  <div className="font-medium">#{cargo.cargo_number}</div>
                                  <div className="text-sm text-gray-600">{cargo.cargo_name || 'Груз'}</div>
                                  <div className="text-sm font-medium text-red-600">
                                    {cargo.declared_value} ₽
                                  </div>
                                </div>
                                <Button size="sm" variant="outline">
                                  Оплатить
                                </Button>
                              </div>
                            ))
                          ) : (
                            <p className="text-gray-500 text-center py-4">Все грузы оплачены!</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Quick Actions */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Быстрые действия</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Button 
                          className="h-20 flex-col" 
                          variant="outline"
                          onClick={() => setActiveTab('create-order')}
                        >
                          <Plus className="h-6 w-6 mb-2" />
                          Оформить груз
                        </Button>
                        <Button 
                          className="h-20 flex-col" 
                          variant="outline"
                          onClick={() => setActiveTab('cargo')}
                        >
                          <Package className="h-6 w-6 mb-2" />
                          Отследить груз
                        </Button>
                        <Button 
                          className="h-20 flex-col" 
                          variant="outline"
                          onClick={() => setActiveTab('contact')}
                        >
                          <MessageCircle className="h-6 w-6 mb-2" />
                          Связаться с нами
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* Create Cargo Order Tab */}
                <TabsContent value="create-order" className="space-y-6">
                  <div className="max-w-4xl mx-auto">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Plus className="mr-2 h-5 w-5 text-blue-600" />
                          Оформление груза
                        </CardTitle>
                        <CardDescription>
                          Рассчитайте стоимость и оформите груз для доставки
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleCreateCargoOrder} className="space-y-6">
                          {/* Основная информация о грузе */}
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="space-y-4">
                              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
                                Информация о грузе
                              </h3>
                              
                              <div>
                                <Label htmlFor="cargo_name">Название груза *</Label>
                                <Input
                                  id="cargo_name"
                                  value={cargoOrderForm.cargo_name}
                                  onChange={(e) => setCargoOrderForm({...cargoOrderForm, cargo_name: e.target.value})}
                                  placeholder="Документы, одежда, подарки..."
                                  required
                                />
                              </div>

                              <div>
                                <Label htmlFor="description">Описание содержимого *</Label>
                                <Textarea
                                  id="description"
                                  value={cargoOrderForm.description}
                                  onChange={(e) => setCargoOrderForm({...cargoOrderForm, description: e.target.value})}
                                  placeholder="Подробное описание содержимого груза"
                                  required
                                />
                              </div>

                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <Label htmlFor="weight">Вес (кг) *</Label>
                                  <Input
                                    id="weight"
                                    type="number"
                                    step="0.1"
                                    min="0.1"
                                    max="10000"
                                    value={cargoOrderForm.weight}
                                    onChange={(e) => {
                                      setCargoOrderForm({...cargoOrderForm, weight: e.target.value});
                                      setCostCalculation(null);
                                    }}
                                    placeholder="5.0"
                                    required
                                  />
                                </div>
                                <div>
                                  <Label htmlFor="declared_value">Объявленная стоимость (₽) *</Label>
                                  <Input
                                    id="declared_value"
                                    type="number"
                                    min="100"
                                    max="10000000"
                                    value={cargoOrderForm.declared_value}
                                    onChange={(e) => {
                                      setCargoOrderForm({...cargoOrderForm, declared_value: e.target.value});
                                      setCostCalculation(null);
                                    }}
                                    placeholder="25000"
                                    required
                                  />
                                </div>
                              </div>

                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <Label htmlFor="route">Маршрут *</Label>
                                  <Select 
                                    value={cargoOrderForm.route} 
                                    onValueChange={(value) => {
                                      handleRouteChange(value); // Используем новую функцию
                                      setCostCalculation(null);
                                    }}
                                  >
                                    <SelectTrigger>
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {deliveryOptions?.routes?.map((route) => (
                                        <SelectItem key={route.value} value={route.value}>
                                          {route.label} ({route.base_days} дней)
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                </div>
                                <div>
                                  <Label htmlFor="delivery_type">Тип доставки *</Label>
                                  <Select 
                                    value={cargoOrderForm.delivery_type} 
                                    onValueChange={(value) => {
                                      setCargoOrderForm({...cargoOrderForm, delivery_type: value});
                                      setCostCalculation(null);
                                    }}
                                  >
                                    <SelectTrigger>
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {deliveryOptions?.delivery_types?.map((type) => (
                                        <SelectItem key={type.value} value={type.value}>
                                          {type.label}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>
                            </div>

                            <div className="space-y-4">
                              <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
                                Информация о получателе
                              </h3>
                              
                              <div>
                                <Label htmlFor="recipient_full_name">ФИО получателя *</Label>
                                <Input
                                  id="recipient_full_name"
                                  value={cargoOrderForm.recipient_full_name}
                                  onChange={(e) => setCargoOrderForm({...cargoOrderForm, recipient_full_name: e.target.value})}
                                  placeholder="Алиев Фарход Рахимович"
                                  required
                                />
                              </div>

                              <div>
                                <Label htmlFor="recipient_phone">Телефон получателя *</Label>
                                <Input
                                  id="recipient_phone"
                                  type="tel"
                                  value={cargoOrderForm.recipient_phone}
                                  onChange={(e) => setCargoOrderForm({...cargoOrderForm, recipient_phone: e.target.value})}
                                  placeholder="+992901234567"
                                  required
                                />
                              </div>

                              <div>
                                <Label htmlFor="recipient_address">Адрес получателя *</Label>
                                <Input
                                  id="recipient_address"
                                  value={cargoOrderForm.recipient_address}
                                  onChange={(e) => setCargoOrderForm({...cargoOrderForm, recipient_address: e.target.value})}
                                  placeholder="ул. Рудаки, 15, кв. 25"
                                  required
                                />
                              </div>

                              <div>
                                <Label htmlFor="recipient_city">Город получателя *</Label>
                                <Input
                                  id="recipient_city"
                                  value={cargoOrderForm.recipient_city}
                                  onChange={(e) => setCargoOrderForm({...cargoOrderForm, recipient_city: e.target.value})}
                                  placeholder="Душанбе"
                                  required
                                />
                              </div>
                            </div>
                          </div>

                          {/* Дополнительные услуги */}
                          <div className="border-t pt-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                              Дополнительные услуги
                            </h3>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                              {/* Страхование */}
                              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                                <input
                                  type="checkbox"
                                  id="insurance_requested"
                                  checked={cargoOrderForm.insurance_requested}
                                  onChange={(e) => {
                                    setCargoOrderForm({
                                      ...cargoOrderForm, 
                                      insurance_requested: e.target.checked,
                                      insurance_value: e.target.checked ? cargoOrderForm.declared_value : ''
                                    });
                                    setCostCalculation(null);
                                  }}
                                  className="rounded"
                                />
                                <div className="flex-1">
                                  <Label htmlFor="insurance_requested" className="font-medium">
                                    Страхование
                                  </Label>
                                  <p className="text-sm text-gray-600">
                                    0.5% от стоимости, мин. 500 ₽
                                  </p>
                                  {cargoOrderForm.insurance_requested && (
                                    <Input
                                      type="number"
                                      value={cargoOrderForm.insurance_value}
                                      onChange={(e) => {
                                        setCargoOrderForm({...cargoOrderForm, insurance_value: e.target.value});
                                        setCostCalculation(null);
                                      }}
                                      placeholder="Сумма страхования"
                                      className="mt-2"
                                    />
                                  )}
                                </div>
                              </div>

                              {/* Упаковка */}
                              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                                <input
                                  type="checkbox"
                                  id="packaging_service"
                                  checked={cargoOrderForm.packaging_service}
                                  onChange={(e) => {
                                    setCargoOrderForm({...cargoOrderForm, packaging_service: e.target.checked});
                                    setCostCalculation(null);
                                  }}
                                  className="rounded"
                                />
                                <div>
                                  <Label htmlFor="packaging_service" className="font-medium">
                                    Упаковка
                                  </Label>
                                  <p className="text-sm text-gray-600">
                                    Профессиональная упаковка - 800 ₽
                                  </p>
                                </div>
                              </div>

                              {/* Забор на дому */}
                              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                                <input
                                  type="checkbox"
                                  id="home_pickup"
                                  checked={cargoOrderForm.home_pickup}
                                  onChange={(e) => {
                                    setCargoOrderForm({...cargoOrderForm, home_pickup: e.target.checked});
                                    setCostCalculation(null);
                                  }}
                                  className="rounded"
                                />
                                <div>
                                  <Label htmlFor="home_pickup" className="font-medium">
                                    Забор на дому
                                  </Label>
                                  <p className="text-sm text-gray-600">
                                    Заберем груз по адресу - 1500 ₽
                                  </p>
                                </div>
                              </div>

                              {/* Доставка на дом */}
                              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                                <input
                                  type="checkbox"
                                  id="home_delivery"
                                  checked={cargoOrderForm.home_delivery}
                                  onChange={(e) => {
                                    setCargoOrderForm({...cargoOrderForm, home_delivery: e.target.checked});
                                    setCostCalculation(null);
                                  }}
                                  className="rounded"
                                />
                                <div>
                                  <Label htmlFor="home_delivery" className="font-medium">
                                    Доставка на дом
                                  </Label>
                                  <p className="text-sm text-gray-600">
                                    Доставим груз получателю - 1200 ₽
                                  </p>
                                </div>
                              </div>

                              {/* Хрупкий груз */}
                              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                                <input
                                  type="checkbox"
                                  id="fragile"
                                  checked={cargoOrderForm.fragile}
                                  onChange={(e) => {
                                    setCargoOrderForm({...cargoOrderForm, fragile: e.target.checked});
                                    setCostCalculation(null);
                                  }}
                                  className="rounded"
                                />
                                <div>
                                  <Label htmlFor="fragile" className="font-medium">
                                    Хрупкий груз
                                  </Label>
                                  <p className="text-sm text-gray-600">
                                    Особая осторожность - 500 ₽
                                  </p>
                                </div>
                              </div>

                              {/* Температурный режим */}
                              <div className="flex items-center space-x-2 p-4 border rounded-lg">
                                <input
                                  type="checkbox"
                                  id="temperature_sensitive"
                                  checked={cargoOrderForm.temperature_sensitive}
                                  onChange={(e) => {
                                    setCargoOrderForm({...cargoOrderForm, temperature_sensitive: e.target.checked});
                                    setCostCalculation(null);
                                  }}
                                  className="rounded"
                                />
                                <div>
                                  <Label htmlFor="temperature_sensitive" className="font-medium">
                                    Температурный режим
                                  </Label>
                                  <p className="text-sm text-gray-600">
                                    Контроль температуры - 800 ₽
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Специальные инструкции */}
                          <div>
                            <Label htmlFor="special_instructions">Специальные инструкции</Label>
                            <Textarea
                              id="special_instructions"
                              value={cargoOrderForm.special_instructions}
                              onChange={(e) => setCargoOrderForm({...cargoOrderForm, special_instructions: e.target.value})}
                              placeholder="Дополнительные требования или инструкции..."
                            />
                          </div>

                          {/* Расчет стоимости */}
                          <div className="border-t pt-6">
                            <div className="flex items-center justify-between mb-4">
                              <h3 className="text-lg font-semibold text-gray-900">
                                Стоимость доставки
                              </h3>
                              <Button 
                                type="button"
                                variant="outline"
                                onClick={calculateCargoCost}
                                disabled={isCalculating || !cargoOrderForm.weight || !cargoOrderForm.declared_value || !cargoOrderForm.cargo_name}
                              >
                                <Calculator className="mr-2 h-4 w-4" />
                                {isCalculating ? 'Расчет...' : 'Рассчитать стоимость'}
                              </Button>
                            </div>

                            {costCalculation && (
                              <div className="bg-blue-50 p-6 rounded-lg">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                  <div>
                                    <h4 className="font-semibold mb-3">Детализация стоимости:</h4>
                                    <div className="space-y-2">
                                      {Object.entries(costCalculation.breakdown).map(([key, value]) => (
                                        <div key={key} className="flex justify-between text-sm">
                                          <span>{key}:</span>
                                          <span className="font-medium">{value}{typeof value === 'number' ? ' ₽' : ''}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-3xl font-bold text-blue-600 mb-2">
                                      {costCalculation.calculation.total_cost} ₽
                                    </div>
                                    <div className="text-lg text-gray-600 mb-2">
                                      Срок доставки: {costCalculation.calculation.delivery_time_days} дней
                                    </div>
                                    <div className="text-sm text-gray-500">
                                      Маршрут: {costCalculation.route_info.route.replace('_', ' → ')}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Кнопки */}
                          <div className="flex items-center justify-between pt-6 border-t">
                            <Button 
                              type="button" 
                              variant="outline"
                              onClick={() => {
                                setCargoOrderForm({
                                  cargo_name: '',
                                  description: '',
                                  weight: '',
                                  declared_value: '',
                                  recipient_full_name: '',
                                  recipient_phone: '',
                                  recipient_address: '',
                                  recipient_city: '',
                                  route: 'moscow_dushanbe',
                                  delivery_type: 'standard',
                                  insurance_requested: false,
                                  insurance_value: '',
                                  packaging_service: false,
                                  home_pickup: false,
                                  home_delivery: false,
                                  fragile: false,
                                  temperature_sensitive: false,
                                  special_instructions: ''
                                });
                                setCostCalculation(null);
                              }}
                            >
                              Очистить форму
                            </Button>
                            <Button 
                              type="submit" 
                              className="bg-blue-600 hover:bg-blue-700"
                              disabled={!costCalculation}
                            >
                              <Package className="mr-2 h-4 w-4" />
                              Оформить груз
                            </Button>
                          </div>
                        </form>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* Cargo Tab */}
                <TabsContent value="cargo" className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold">Мои грузы</h2>
                    <div className="flex items-center space-x-2">
                      <Select defaultValue="all" onValueChange={(value) => fetchClientCargo(value === 'all' ? null : value)}>
                        <SelectTrigger className="w-40">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Все статусы</SelectItem>
                          <SelectItem value="accepted">Принят</SelectItem>
                          <SelectItem value="placed_in_warehouse">На складе</SelectItem>
                          <SelectItem value="on_transport">На транспорте</SelectItem>
                          <SelectItem value="in_transit">В пути</SelectItem>
                          <SelectItem value="delivered">Доставлен</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button 
                        variant="outline" 
                        onClick={() => fetchClientCargo()}
                      >
                        Обновить
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {clientCargo.length === 0 ? (
                      <Card>
                        <CardContent className="p-8 text-center">
                          <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                          <p className="text-gray-500">У вас пока нет грузов</p>
                          <Button 
                            className="mt-4" 
                            onClick={() => setActiveTab('requests')}
                          >
                            Подать заявку на груз
                          </Button>
                        </CardContent>
                      </Card>
                    ) : (
                      clientCargo.map((cargo) => (
                        <Card key={cargo.id}>
                          <CardContent className="p-6">
                            <div className="flex items-center justify-between mb-4">
                              <div>
                                <h3 className="font-semibold text-lg">#{cargo.cargo_number}</h3>
                                <p className="text-gray-600">{cargo.cargo_name || 'Груз'}</p>
                              </div>
                              <Badge variant={cargo.status === 'delivered' ? 'default' : 'outline'}>
                                {cargo.status}
                              </Badge>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                              <div>
                                <p className="text-sm text-gray-600">Получатель:</p>
                                <p className="font-medium">{cargo.recipient_full_name}</p>
                                <p className="text-sm text-gray-600">{cargo.recipient_phone}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Вес:</p>
                                <p className="font-medium">{cargo.weight} кг</p>
                                <p className="text-sm text-gray-600">Стоимость: {cargo.declared_value} ₽</p>
                              </div>
                            </div>

                            {cargo.location_description && (
                              <div className="mb-4">
                                <p className="text-sm text-gray-600">Местоположение:</p>
                                <p className="font-medium">{cargo.location_description}</p>
                              </div>
                            )}

                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-4 text-sm text-gray-600">
                                {cargo.tracking_code && (
                                  <span className="flex items-center">
                                    <QrCode className="mr-1 h-4 w-4" />
                                    Трекинг: {cargo.tracking_code}
                                  </span>
                                )}
                                {cargo.photo_count > 0 && (
                                  <span className="flex items-center">
                                    <Camera className="mr-1 h-4 w-4" />
                                    {cargo.photo_count} фото
                                  </span>
                                )}
                                {cargo.comment_count > 0 && (
                                  <span className="flex items-center">
                                    <MessageCircle className="mr-1 h-4 w-4" />
                                    {cargo.comment_count} комментариев
                                  </span>
                                )}
                              </div>
                              <div className="flex space-x-2">
                                <Button 
                                  variant="outline" 
                                  size="sm"
                                  onClick={() => openRepeatOrder(cargo)}
                                  className="text-green-600 hover:text-green-700"
                                  title="Повторить заказ с теми же данными"
                                >
                                  <Copy className="mr-1 h-4 w-4" />
                                  Повторить
                                </Button>
                                <Button 
                                  variant="outline" 
                                  size="sm"
                                  onClick={() => fetchClientCargoDetails(cargo.id)}
                                >
                                  <Eye className="mr-1 h-4 w-4" />
                                  Подробнее
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </div>
                </TabsContent>

                {/* Keep existing Requests and Contact tabs */}
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
                                required
                              />
                            </div>
                          </div>
                          <div>
                            <Label htmlFor="recipient_address">Адрес получателя</Label>
                            <Input
                              id="recipient_address"
                              value={requestForm.recipient_address}
                              onChange={(e) => setRequestForm({...requestForm, recipient_address: e.target.value})}
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="pickup_address">Адрес забора груза</Label>
                            <Input
                              id="pickup_address"
                              value={requestForm.pickup_address}
                              onChange={(e) => setRequestForm({...requestForm, pickup_address: e.target.value})}
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="cargo_name">Название груза</Label>
                            <Input
                              id="cargo_name"
                              value={requestForm.cargo_name}
                              onChange={(e) => setRequestForm({...requestForm, cargo_name: e.target.value})}
                              required
                            />
                          </div>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <Label htmlFor="weight">Вес (кг)</Label>
                              <Input
                                id="weight"
                                type="number"
                                step="0.1"
                                value={requestForm.weight}
                                onChange={(e) => setRequestForm({...requestForm, weight: e.target.value})}
                                required
                              />
                            </div>
                            <div>
                              <Label htmlFor="declared_value">Объявленная стоимость (₽)</Label>
                              <Input
                                id="declared_value"
                                type="number"
                                value={requestForm.declared_value}
                                onChange={(e) => setRequestForm({...requestForm, declared_value: e.target.value})}
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
                              required
                            />
                          </div>
                          <Button type="submit" className="w-full">
                            Подать заявку
                          </Button>
                        </form>
                      </CardContent>
                    </Card>

                    {/* Мои заявки */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <FileText className="mr-2 h-5 w-5" />
                          Мои заявки
                        </CardTitle>
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
                                    <div className="font-medium">{request.recipient_full_name}</div>
                                    <div className="text-sm text-gray-600">{request.recipient_phone}</div>
                                  </div>
                                  <Badge variant={request.status === 'approved' ? 'default' : 'outline'}>
                                    {request.status}
                                  </Badge>
                                </div>
                                <div className="text-sm text-gray-600 mb-2">
                                  {request.description}
                                </div>
                                <div className="flex justify-between text-sm">
                                  <span>Вес: {request.weight} кг</span>
                                  <span>Стоимость: {request.declared_value} ₽</span>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="contact" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <MessageCircle className="mr-2 h-5 w-5" />
                        Связаться с нами
                      </CardTitle>
                      <CardDescription>
                        Выберите удобный способ связи
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Button className="h-20 flex-col" variant="outline">
                          <MessageCircle className="h-6 w-6 mb-2" />
                          WhatsApp
                        </Button>
                        <Button className="h-20 flex-col" variant="outline">
                          <MessageCircle className="h-6 w-6 mb-2" />
                          Telegram
                        </Button>
                        <Button className="h-20 flex-col" variant="outline">
                          <MessageCircle className="h-6 w-6 mb-2" />
                          Онлайн чат
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          ) : (
            /* Для админа и оператора склада - новый интерфейс с боковым меню */
            <div className="space-y-6">
              
              {/* Шапка с поиском и уведомлениями */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    
                    {/* Поиск с расширенными функциями */}
                    <div className="flex-1 max-w-md relative">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                        <Input
                          placeholder="Поиск по номеру, ФИО, телефону..."
                          value={searchQuery}
                          onChange={(e) => handleSearchInput(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              handleAdvancedSearch(searchQuery);
                            }
                          }}
                          className="pl-10 pr-20"
                        />
                        
                        {/* Кнопка расширенного поиска */}
                        <Button
                          size="sm"
                          variant="outline"
                          className="absolute right-1 top-1/2 transform -translate-y-1/2"
                          onClick={() => setAdvancedSearchOpen(!advancedSearchOpen)}
                        >
                          <Filter className="h-4 w-4" />
                        </Button>
                        
                        {searchQuery && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="absolute right-12 top-1/2 transform -translate-y-1/2"
                            onClick={clearSearch}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>

                      {/* Автодополнение */}
                      {showSuggestions && searchSuggestions.length > 0 && (
                        <div className="absolute z-50 mt-1 w-full bg-white border rounded-lg shadow-lg">
                          {searchSuggestions.map((suggestion, index) => (
                            <div
                              key={index}
                              className="p-2 hover:bg-gray-100 cursor-pointer text-sm"
                              onClick={() => selectSearchSuggestion(suggestion)}
                            >
                              <Search className="inline mr-2 h-3 w-3 text-gray-400" />
                              {suggestion}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Расширенные фильтры */}
                      {advancedSearchOpen && (
                        <div className="absolute z-50 mt-2 w-96 bg-white border rounded-lg shadow-lg p-4">
                          <div className="space-y-4">
                            <h3 className="font-semibold text-sm">Расширенные фильтры</h3>
                            
                            {/* Фильтры для грузов */}
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <Label className="text-xs">Статус груза</Label>
                                <Select 
                                  value={searchFilters.cargo_status} 
                                  onValueChange={(value) => setSearchFilters({...searchFilters, cargo_status: value})}
                                >
                                  <SelectTrigger className="h-8">
                                    <SelectValue placeholder="Любой" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="">Любой</SelectItem>
                                    <SelectItem value="accepted">Принят</SelectItem>
                                    <SelectItem value="in_transit">В пути</SelectItem>
                                    <SelectItem value="delivered">Доставлен</SelectItem>
                                    <SelectItem value="returned">Возвращен</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              
                              <div>
                                <Label className="text-xs">Оплата</Label>
                                <Select 
                                  value={searchFilters.payment_status} 
                                  onValueChange={(value) => setSearchFilters({...searchFilters, payment_status: value})}
                                >
                                  <SelectTrigger className="h-8">
                                    <SelectValue placeholder="Любая" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="">Любая</SelectItem>
                                    <SelectItem value="pending">Ожидается</SelectItem>
                                    <SelectItem value="paid">Оплачен</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <Label className="text-xs">Маршрут</Label>
                                <Select 
                                  value={searchFilters.route} 
                                  onValueChange={(value) => setSearchFilters({...searchFilters, route: value})}
                                >
                                  <SelectTrigger className="h-8">
                                    <SelectValue placeholder="Любой" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="">Любой</SelectItem>
                                    <SelectItem value="moscow_to_tajikistan">Москва → Таджикистан</SelectItem>
                                    <SelectItem value="tajikistan_to_moscow">Таджикистан → Москва</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              
                              <div>
                                <Label className="text-xs">Сортировка</Label>
                                <Select 
                                  value={searchFilters.sort_by} 
                                  onValueChange={(value) => setSearchFilters({...searchFilters, sort_by: value})}
                                >
                                  <SelectTrigger className="h-8">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="created_at">По дате</SelectItem>
                                    <SelectItem value="relevance_score">По релевантности</SelectItem>
                                    <SelectItem value="weight">По весу</SelectItem>
                                    <SelectItem value="declared_value">По стоимости</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>

                            {/* Поля для телефонов */}
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <Label className="text-xs">Телефон отправителя</Label>
                                <Input
                                  className="h-8"
                                  placeholder="+7..."
                                  value={searchFilters.sender_phone}
                                  onChange={(e) => setSearchFilters({...searchFilters, sender_phone: e.target.value})}
                                />
                              </div>
                              <div>
                                <Label className="text-xs">Телефон получателя</Label>
                                <Input
                                  className="h-8"
                                  placeholder="+992..."
                                  value={searchFilters.recipient_phone}
                                  onChange={(e) => setSearchFilters({...searchFilters, recipient_phone: e.target.value})}
                                />
                              </div>
                            </div>

                            {/* Диапазон дат */}
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <Label className="text-xs">От даты</Label>
                                <Input
                                  type="date"
                                  className="h-8"
                                  value={searchFilters.date_from}
                                  onChange={(e) => setSearchFilters({...searchFilters, date_from: e.target.value})}
                                />
                              </div>
                              <div>
                                <Label className="text-xs">До даты</Label>
                                <Input
                                  type="date"
                                  className="h-8"
                                  value={searchFilters.date_to}
                                  onChange={(e) => setSearchFilters({...searchFilters, date_to: e.target.value})}
                                />
                              </div>
                            </div>

                            <div className="flex justify-between">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSearchFilters({
                                    cargo_status: '',
                                    payment_status: '',
                                    processing_status: '',
                                    route: '',
                                    sender_phone: '',
                                    recipient_phone: '',
                                    date_from: '',
                                    date_to: '',
                                    user_role: '',
                                    user_status: null,
                                    sort_by: 'created_at',
                                    sort_order: 'desc'
                                  });
                                }}
                              >
                                Сбросить
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => {
                                  handleAdvancedSearch(searchQuery, searchFilters);
                                  setAdvancedSearchOpen(false);
                                }}
                                disabled={searchLoading}
                              >
                                {searchLoading ? 'Поиск...' : 'Применить'}
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* Результаты поиска */}
                      {showSearchResults && (
                        <div className="absolute z-40 mt-2 w-full bg-white border rounded-lg shadow-lg max-h-80 overflow-y-auto">
                          {/* Информация о поиске */}
                          {searchTime > 0 && (
                            <div className="px-3 py-2 bg-gray-50 border-b text-xs text-gray-600">
                              Найдено {searchResults.length} результатов за {searchTime}мс
                            </div>
                          )}
                          
                          {!Array.isArray(searchResults) || searchResults.length === 0 ? (
                            <div className="p-4 text-gray-500 text-center">Ничего не найдено</div>
                          ) : (
                            searchResults.map((result) => (
                              <div
                                key={result.id}
                                className="p-3 border-b hover:bg-gray-50 cursor-pointer"
                                onClick={() => {
                                  if (result.type === 'cargo') {
                                    fetchCargoDetails(result.id).then(cargoDetails => {
                                      setSelectedCellCargo(cargoDetails);
                                      setCargoDetailModal(true);
                                      clearSearch();
                                    });
                                  } else if (result.type === 'user') {
                                    // Открыть профиль пользователя
                                    console.log('Open user profile:', result.id);
                                  } else if (result.type === 'warehouse') {
                                    // Открыть склад
                                    console.log('Open warehouse:', result.id);
                                  }
                                }}
                              >
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="font-medium text-sm">{result.title}</div>
                                    <div className="text-xs text-gray-600">{result.subtitle}</div>
                                    
                                    {/* Дополнительная информация в зависимости от типа */}
                                    {result.type === 'cargo' && (
                                      <div className="mt-1 text-xs text-gray-500">
                                        {result.details.weight && `${result.details.weight} кг`}
                                        {result.details.declared_value && ` • ${result.details.declared_value} руб`}
                                        {result.details.status && ` • ${result.details.status}`}
                                      </div>
                                    )}
                                    
                                    {result.type === 'warehouse' && (
                                      <div className="mt-1 text-xs text-gray-500">
                                        {result.details.cargo_count} грузов на складе
                                      </div>
                                    )}
                                  </div>
                                  
                                  <div className="ml-2 text-right">
                                    <Badge variant="outline" className="text-xs">
                                      {result.type === 'cargo' ? 'Груз' : 
                                       result.type === 'user' ? 'Пользователь' : 'Склад'}
                                    </Badge>
                                    {result.relevance_score && (
                                      <div className="text-xs text-gray-400 mt-1">
                                        {result.relevance_score.toFixed(0)}%
                                      </div>
                                    )}
                                  </div>
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
                      <div className="text-2xl font-bold">{users && Array.isArray(users) ? users.filter(u => u.is_active !== false).length : 0}</div>
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

              {/* Личный кабинет */}
              {activeSection === 'personal-dashboard' && (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <User className="mr-2 h-5 w-5" />
                        Личный кабинет
                      </CardTitle>
                      <CardDescription>
                        Ваша персональная информация и история операций
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between mb-6">
                        <Button 
                          onClick={fetchPersonalDashboard}
                          disabled={dashboardLoading}
                        >
                          {dashboardLoading ? 'Загрузка...' : 'Обновить данные'}
                        </Button>
                      </div>
                      
                      {personalDashboardData && (
                        <div className="space-y-6">
                          {/* Информация о пользователе */}
                          <div className="bg-gray-50 p-6 rounded-lg">
                            <h3 className="text-lg font-semibold mb-4">Информация о пользователе</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <label className="text-sm font-medium text-gray-500">Номер пользователя</label>
                                <p className="text-lg">{personalDashboardData.user_info.user_number}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-gray-500">ФИО</label>
                                <p className="text-lg">{personalDashboardData.user_info.full_name}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-gray-500">Телефон</label>
                                <p className="text-lg">{personalDashboardData.user_info.phone}</p>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-gray-500">Роль</label>
                                <Badge variant="outline">{getRoleLabel(personalDashboardData.user_info.role)}</Badge>
                              </div>
                              <div>
                                <label className="text-sm font-medium text-gray-500">Дата регистрации</label>
                                <p className="text-lg">{new Date(personalDashboardData.user_info.created_at).toLocaleDateString('ru-RU')}</p>
                              </div>
                            </div>
                          </div>

                          {/* Заявки на грузы */}
                          <div>
                            <h3 className="text-lg font-semibold mb-4 flex items-center">
                              <FileText className="mr-2 h-5 w-5" />
                              Мои заявки на грузы ({personalDashboardData.cargo_requests.length})
                            </h3>
                            {personalDashboardData.cargo_requests.length > 0 ? (
                              <div className="space-y-3">
                                {personalDashboardData.cargo_requests.slice(0, 10).map((request, index) => (
                                  <div key={index} className="bg-white border rounded-lg p-4">
                                    <div className="flex justify-between items-start">
                                      <div>
                                        <h4 className="font-medium">{request.cargo_name}</h4>
                                        <p className="text-sm text-gray-600">
                                          Вес: {request.weight} кг | Стоимость: {request.declared_value} руб
                                        </p>
                                        <p className="text-sm text-gray-600">
                                          Получатель: {request.recipient_name} ({request.recipient_phone})
                                        </p>
                                      </div>
                                      <div className="text-right">
                                        <Badge variant="secondary">{request.status}</Badge>
                                        <p className="text-xs text-gray-500 mt-1">
                                          {new Date(request.created_at).toLocaleDateString('ru-RU')}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-gray-500">У вас пока нет заявок на грузы</p>
                            )}
                          </div>

                          {/* Отправленные грузы */}
                          <div>
                            <h3 className="text-lg font-semibold mb-4 flex items-center">
                              <Package className="mr-2 h-5 w-5" />
                              Отправленные грузы ({personalDashboardData.sent_cargo.length})
                            </h3>
                            {personalDashboardData.sent_cargo.length > 0 ? (
                              <div className="space-y-3">
                                {personalDashboardData.sent_cargo.slice(0, 10).map((cargo, index) => (
                                  <div key={index} className="bg-white border rounded-lg p-4">
                                    <div className="flex justify-between items-start">
                                      <div>
                                        <h4 className="font-medium">
                                          {cargo.cargo_number} - {cargo.cargo_name}
                                        </h4>
                                        <p className="text-sm text-gray-600">
                                          Вес: {cargo.weight} кг | Стоимость: {cargo.declared_value} руб
                                        </p>
                                        <p className="text-sm text-gray-600">
                                          Получатель: {cargo.recipient_name} ({cargo.recipient_phone})
                                        </p>
                                        {cargo.created_by_operator && (
                                          <p className="text-sm text-gray-500">
                                            Принято оператором: {cargo.created_by_operator}
                                          </p>
                                        )}
                                      </div>
                                      <div className="text-right">
                                        <div className="space-y-1">
                                          <Badge variant="default">{cargo.status}</Badge>
                                          {cargo.payment_status && (
                                            <Badge variant="secondary" className="block">
                                              {cargo.payment_status}
                                            </Badge>
                                          )}
                                          {cargo.processing_status && (
                                            <Badge variant="outline" className="block">
                                              {cargo.processing_status}
                                            </Badge>
                                          )}
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">
                                          {new Date(cargo.created_at).toLocaleDateString('ru-RU')}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-gray-500">У вас пока нет отправленных грузов</p>
                            )}
                          </div>

                          {/* Полученные грузы */}
                          <div>
                            <h3 className="text-lg font-semibold mb-4 flex items-center">
                              <Truck className="mr-2 h-5 w-5" />
                              Полученные грузы ({personalDashboardData.received_cargo.length})
                            </h3>
                            {personalDashboardData.received_cargo.length > 0 ? (
                              <div className="space-y-3">
                                {personalDashboardData.received_cargo.slice(0, 10).map((cargo, index) => (
                                  <div key={index} className="bg-white border rounded-lg p-4">
                                    <div className="flex justify-between items-start">
                                      <div>
                                        <h4 className="font-medium">
                                          {cargo.cargo_number} - {cargo.cargo_name}
                                        </h4>
                                        <p className="text-sm text-gray-600">
                                          Вес: {cargo.weight} кг | Стоимость: {cargo.declared_value} руб
                                        </p>
                                        <p className="text-sm text-gray-600">
                                          Отправитель: {cargo.sender_name} ({cargo.sender_phone})
                                        </p>
                                        {cargo.created_by_operator && (
                                          <p className="text-sm text-gray-500">
                                            Принято оператором: {cargo.created_by_operator}
                                          </p>
                                        )}
                                      </div>
                                      <div className="text-right">
                                        <div className="space-y-1">
                                          <Badge variant="default">{cargo.status}</Badge>
                                          {cargo.payment_status && (
                                            <Badge variant="secondary" className="block">
                                              {cargo.payment_status}
                                            </Badge>
                                          )}
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">
                                          {new Date(cargo.created_at).toLocaleDateString('ru-RU')}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-gray-500">У вас пока нет полученных грузов</p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {!personalDashboardData && !dashboardLoading && (
                        <div className="text-center py-8">
                          <User className="mx-auto h-12 w-12 text-gray-400" />
                          <h3 className="mt-4 text-sm font-medium text-gray-900">Данные не загружены</h3>
                          <p className="mt-1 text-sm text-gray-500">
                            Нажмите кнопку "Обновить данные" для загрузки информации
                          </p>
                        </div>
                      )}
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
                        {isFilledFromProfile && profileSourceUser && (
                          <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="flex items-center text-blue-800">
                              <User className="mr-2 h-4 w-4" />
                              <span className="text-sm font-medium">
                                Данные автозаполнены из профиля: {profileSourceUser.full_name} ({profileSourceUser.user_number})
                              </span>
                            </div>
                            <p className="text-xs text-blue-600 mt-1">
                              Данные отправителя и получателя заполнены автоматически. Заполните только грузы.
                            </p>
                          </div>
                        )}
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

                          {/* Переключатель между режимами */}
                          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                            <Label className="flex items-center space-x-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={operatorCargoForm.use_multi_cargo}
                                onChange={(e) => {
                                  setOperatorCargoForm({
                                    ...operatorCargoForm,
                                    use_multi_cargo: e.target.checked
                                  });
                                  if (!e.target.checked) {
                                    setTotalWeight(0);
                                    setTotalCost(0);
                                  }
                                }}
                                className="rounded"
                              />
                              <span className="text-sm font-medium">
                                Несколько видов груза (с калькулятором)
                              </span>
                            </Label>
                          </div>

                          {!operatorCargoForm.use_multi_cargo ? (
                            // Старая форма для одного груза
                            <>
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

                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                              </div>
                            </>
                          ) : (
                            // Новая форма с множественными грузами и калькулятором
                            <>
                              <div className="bg-blue-50 p-4 rounded-lg">
                                <h3 className="font-semibold text-lg mb-3 flex items-center">
                                  <Package className="mr-2 h-5 w-5" />
                                  Список грузов
                                </h3>
                                
                                {operatorCargoForm.cargo_items.map((item, index) => (
                                  <div key={index} className="mb-4 p-4 bg-white rounded border">
                                    <div className="flex items-center justify-between mb-2">
                                      <span className="font-medium text-sm text-gray-600">
                                        Груз #{index + 1}
                                      </span>
                                      {operatorCargoForm.cargo_items.length > 1 && (
                                        <Button
                                          type="button"
                                          variant="outline"
                                          size="sm"
                                          onClick={() => removeCargoItem(index)}
                                        >
                                          <X className="h-4 w-4" />
                                        </Button>
                                      )}
                                    </div>
                                    
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                      <div>
                                        <Label>Название груза</Label>
                                        <Input
                                          value={item.cargo_name}
                                          onChange={(e) => updateCargoItem(index, 'cargo_name', e.target.value)}
                                          placeholder="Документы, одежда, электроника"
                                          required
                                        />
                                      </div>
                                      <div>
                                        <Label>Вес (кг)</Label>
                                        <Input
                                          type="number"
                                          step="0.1"
                                          min="0"
                                          value={item.weight}
                                          onChange={(e) => updateCargoItem(index, 'weight', e.target.value)}
                                          placeholder="10.5"
                                          required
                                        />
                                      </div>
                                      <div>
                                        <Label>Цена за кг (руб.)</Label>
                                        <Input
                                          type="number"
                                          step="0.01"
                                          min="0"
                                          value={item.price_per_kg}
                                          onChange={(e) => updateCargoItem(index, 'price_per_kg', e.target.value)}
                                          placeholder="100"
                                          required
                                        />
                                      </div>
                                    </div>
                                    
                                    {/* Показываем промежуточный расчет для каждого груза */}
                                    {item.weight && item.price_per_kg && (
                                      <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                                        <span className="text-gray-600">
                                          Стоимость: {parseFloat(item.weight)} кг × {parseFloat(item.price_per_kg)} руб/кг = 
                                          <span className="font-semibold text-green-600 ml-1">
                                            {(parseFloat(item.weight) * parseFloat(item.price_per_kg)).toFixed(2)} руб
                                          </span>
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                ))}
                                
                                <Button
                                  type="button"
                                  variant="outline"
                                  onClick={addCargoItem}
                                  className="w-full"
                                >
                                  <Plus className="mr-2 h-4 w-4" />
                                  Добавить еще груз
                                </Button>
                              </div>

                              {/* Калькулятор стоимости с детальной разбивкой */}
                              <div className="bg-green-50 p-4 rounded-lg">
                                <h3 className="font-semibold text-lg mb-3 flex items-center">
                                  <Calculator className="mr-2 h-5 w-5" />
                                  Калькулятор стоимости
                                </h3>
                                
                                {/* Детальная разбивка по каждому грузу */}
                                {cargoBreakdown.length > 0 && (
                                  <div className="mb-4">
                                    <h4 className="font-medium text-sm text-gray-700 mb-2">Детальная разбивка:</h4>
                                    <div className="space-y-2">
                                      {cargoBreakdown.map((item, index) => (
                                        <div key={index} className="bg-white p-3 rounded border-l-4 border-blue-400">
                                          <div className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-gray-700">
                                              Груз #{item.index}: {item.name}
                                            </span>
                                            <span className="text-sm font-bold text-green-600">
                                              {item.cost.toFixed(2)} руб
                                            </span>
                                          </div>
                                          <div className="text-xs text-gray-500 mt-1">
                                            {item.weight.toFixed(1)} кг × {item.pricePerKg.toFixed(2)} руб/кг
                                          </div>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Общие итоги */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <div className="bg-white p-3 rounded border">
                                    <div className="text-sm text-gray-600">Общий вес</div>
                                    <div className="text-2xl font-bold text-blue-600">
                                      {totalWeight.toFixed(1)} кг
                                    </div>
                                  </div>
                                  <div className="bg-white p-3 rounded border">
                                    <div className="text-sm text-gray-600">Общая стоимость</div>
                                    <div className="text-2xl font-bold text-green-600">
                                      {totalCost.toFixed(2)} руб
                                    </div>
                                  </div>
                                </div>

                                {/* Сводка расчетов */}
                                {cargoBreakdown.length > 1 && (
                                  <div className="mt-3 p-2 bg-white rounded text-sm border-t-2 border-green-400">
                                    <div className="font-medium text-gray-700 mb-1">ИТОГО:</div>
                                    {cargoBreakdown.map((item, index) => (
                                      <div key={index} className="flex justify-between text-xs text-gray-600">
                                        <span>{item.name}: {item.weight.toFixed(1)}кг × {item.pricePerKg.toFixed(2)}руб</span>
                                        <span>{item.cost.toFixed(2)}руб</span>
                                      </div>
                                    ))}
                                    <div className="flex justify-between font-bold text-sm text-green-700 mt-1 pt-1 border-t">
                                      <span>Всего: {totalWeight.toFixed(1)} кг</span>
                                      <span>{totalCost.toFixed(2)} руб</span>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </>
                          )}

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

                          {/* Кнопки действий */}
                          <div className="flex flex-col gap-4">
                            {/* Кнопки печати */}
                            <div className="flex gap-2">
                              <Button 
                                type="button" 
                                variant="outline"
                                onClick={handlePrintCurrentInvoice}
                                disabled={!canPrintInvoice()}
                                className="flex-1"
                              >
                                <Printer className="mr-2 h-4 w-4" />
                                Печать накладной
                              </Button>
                              <Button 
                                type="button" 
                                variant="outline"
                                onClick={handlePrintCurrentBarcode}
                                disabled={!canPrintInvoice()}
                                className="flex-1"
                              >
                                <QrCode className="mr-2 h-4 w-4" />
                                Штрих-код
                              </Button>
                            </div>
                            
                            {/* Главная кнопка приема груза */}
                            <Button type="submit" className="w-full" size="lg">
                              <Plus className="mr-2 h-4 w-4" />
                              Принять груз
                            </Button>
                            
                            {/* Информация о статусе */}
                            <div className="text-sm text-gray-600 text-center bg-blue-50 p-3 rounded-lg">
                              <div className="flex items-center justify-center mb-2">
                                <Clock className="mr-2 h-4 w-4" />
                                <span className="font-medium">После приема груз поступает в:</span>
                              </div>
                              <div className="text-blue-800 font-semibold">
                                Касса → Не оплачено
                              </div>
                              <div className="text-xs text-gray-500 mt-1">
                                После оплаты груз автоматически переместится в "Размещение груза"
                              </div>
                            </div>
                          </div>
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
                        
                        {/* Фильтры */}
                        <div className="flex items-center space-x-4 mt-4">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium">Фильтр:</span>
                            <select 
                              value={operatorCargoFilter}
                              onChange={(e) => {
                                setOperatorCargoFilter(e.target.value);
                                setOperatorCargoPage(1); // Сбрасываем на первую страницу при изменении фильтра
                                fetchOperatorCargo(e.target.value, 1, operatorCargoPerPage);
                              }}
                              className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                            >
                              <option value="">Все грузы</option>
                              <option value="new_request">Новые заявки</option>
                              <option value="awaiting_payment">Ожидается оплата</option>
                              <option value="awaiting_placement">Ожидает размещение</option>
                            </select>
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => fetchOperatorCargo(operatorCargoFilter, operatorCargoPage, operatorCargoPerPage)}
                          >
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Обновить
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {operatorCargo.length === 0 ? (
                            <div className="text-center py-8">
                              <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500 mb-4">
                                {operatorCargoFilter 
                                  ? `Нет грузов с фильтром "${operatorCargoFilter === 'new_request' ? 'Новые заявки' : operatorCargoFilter === 'awaiting_payment' ? 'Ожидается оплата' : 'Ожидает размещение'}"` 
                                  : 'Нет принятых грузов'
                                }
                              </p>
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
                                  <TableHead>Статус обработки</TableHead>
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
                                      <div className="flex flex-col space-y-1">
                                        <Badge variant={getProcessingStatusBadgeVariant(item.processing_status || 'payment_pending')}>
                                          {getProcessingStatusLabel(item.processing_status || 'payment_pending')}
                                        </Badge>
                                        {/* Кнопки для изменения статуса */}
                                        <div className="flex space-x-1">
                                          {item.processing_status === 'payment_pending' && (
                                            <Button
                                              size="sm"
                                              onClick={() => handlePaymentAcceptance(item.id, item.cargo_number)}
                                              className="text-xs px-3 py-1 bg-green-600 hover:bg-green-700 text-white font-medium"
                                            >
                                              💰 Оплачен
                                            </Button>
                                          )}
                                          {item.processing_status === 'paid' && (
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              onClick={() => updateCargoProcessingStatus(item.id, 'invoice_printed')}
                                              className="text-xs px-2 py-1"
                                            >
                                              📄 Накладная
                                            </Button>
                                          )}
                                          {item.processing_status === 'invoice_printed' && (
                                            <Button
                                              size="sm"
                                              variant="outline"
                                              onClick={() => updateCargoProcessingStatus(item.id, 'placed')}
                                              className="text-xs px-2 py-1"
                                            >
                                              📦 Разместить
                                            </Button>
                                          )}
                                        </div>
                                      </div>
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
                                      <div className="flex flex-col space-y-1">
                                        <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() => printCargoInvoice(item)}
                                          className="flex items-center"
                                          disabled={!item.processing_status || item.processing_status === 'payment_pending'}
                                        >
                                          <Printer className="mr-1 h-4 w-4" />
                                          Накладная
                                        </Button>
                                        {/* QR код доступен всегда */}
                                        <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() => {
                                            // Показать QR код груза
                                            showAlert('QR код для груза ' + item.cargo_number, 'info');
                                          }}
                                          className="flex items-center text-xs px-2 py-1"
                                        >
                                          <QrCode className="mr-1 h-3 w-3" />
                                          QR
                                        </Button>
                                        
                                        {/* Кнопка быстрого размещения для оплаченных грузов */}
                                        {(item.processing_status === 'paid' || item.processing_status === 'invoice_printed') && !item.warehouse_location && (
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => {
                                              setSelectedCargoForDetailView(item);
                                              setQuickPlacementModal(true);
                                            }}
                                            className="flex items-center text-xs px-2 py-1 bg-green-50 hover:bg-green-100"
                                          >
                                            <Grid3X3 className="mr-1 h-3 w-3" />
                                            Разместить
                                          </Button>
                                        )}
                                        
                                        {/* Кнопка повторного заказа для админов и операторов */}
                                        {(user.role === 'admin' || user.role === 'warehouse_operator') && (
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => openAdminRepeatOrder(item)}
                                            className="flex items-center text-xs px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-600 hover:text-blue-700"
                                            title="Повторить заказ с теми же данными отправителя и получателя"
                                          >
                                            <Copy className="mr-1 h-3 w-3" />
                                            Повторить
                                          </Button>
                                        )}
                                      </div>
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </div>
                        
                        {/* Пагинация для списка грузов */}
                        {operatorCargo.length > 0 && operatorCargoPagination && (
                          <DataPagination
                            pagination={operatorCargoPagination}
                            onPageChange={handleOperatorCargoPageChange}
                            onPerPageChange={handleOperatorCargoPerPageChange}
                          />
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {/* Размещение груза - Улучшенный интерфейс */}
                  {activeTab === 'cargo-placement' && (
                    <div className="space-y-6">
                      <Card>
                        <CardHeader>
                          <CardTitle className="flex items-center">
                            <Grid3X3 className="mr-2 h-5 w-5" />
                            Ожидает размещение
                          </CardTitle>
                          <CardDescription>
                            Оплаченные грузы, готовые к размещению на складе. Автоматически обновляется при принятии оплат.
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Button onClick={() => fetchAvailableCargoForPlacement(availableCargoPage, availableCargoPerPage)} className="mb-4">
                            <RefreshCw className="mr-2 h-4 w-4" />
                            Обновить список грузов
                          </Button>
                          
                          <div className="space-y-4">
                            {availableCargoForPlacement.length === 0 ? (
                              <div className="text-center py-8">
                                <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                                <p className="text-gray-500">Нет грузов, ожидающих размещения</p>
                                <p className="text-sm text-gray-400 mt-2">Оплаченные грузы из "Списка грузов" автоматически появятся здесь</p>
                                <Button 
                                  variant="outline" 
                                  className="mt-4"
                                  onClick={() => setActiveTab('cargo-list')}
                                >
                                  Перейти к списку грузов
                                </Button>
                              </div>
                            ) : (
                              <div className="grid gap-6">
                                {availableCargoForPlacement.map((item) => (
                                  <Card key={item.id} className="border-l-4 border-l-blue-500">
                                    <CardContent className="p-6">
                                      <div className="flex justify-between items-start">
                                        {/* Основная информация о грузе */}
                                        <div className="flex-1">
                                          <div className="flex items-center space-x-4 mb-4">
                                            <h3 className="font-bold text-xl text-blue-600">{item.cargo_number}</h3>
                                            <Badge variant={getProcessingStatusBadgeVariant(item.processing_status)}>
                                              {getProcessingStatusLabel(item.processing_status)}
                                            </Badge>
                                          </div>
                                          
                                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Информация о грузе */}
                                            <div className="space-y-2">
                                              <h4 className="font-semibold text-lg text-gray-700 mb-3">📦 Информация о грузе</h4>
                                              <div className="space-y-1 text-sm">
                                                <p><strong>Наименование:</strong> {item.cargo_name}</p>
                                                <p><strong>Вес:</strong> {item.weight} кг</p>
                                                <p><strong>Стоимость:</strong> {item.declared_value} ₽</p>
                                                <p><strong>Статус:</strong> {getProcessingStatusLabel(item.processing_status)}</p>
                                              </div>
                                            </div>
                                            
                                            {/* Информация об отправителе */}
                                            <div className="space-y-2">
                                              <h4 className="font-semibold text-lg text-gray-700 mb-3">👤 Отправитель</h4>
                                              <div className="space-y-1 text-sm">
                                                <p><strong>Имя:</strong> {item.sender_full_name}</p>
                                                <p><strong>Телефон:</strong> {item.sender_phone}</p>
                                                <p><strong>Принял:</strong> {item.accepting_operator}</p>
                                              </div>
                                            </div>
                                            
                                            {/* Информация о получателе */}
                                            <div className="space-y-2">
                                              <h4 className="font-semibold text-lg text-gray-700 mb-3">📍 Получатель</h4>
                                              <div className="space-y-1 text-sm">
                                                <p><strong>Имя:</strong> {item.recipient_name}</p>
                                                <p><strong>Телефон:</strong> {item.recipient_phone}</p>
                                                <p><strong>Адрес:</strong> {item.recipient_address}</p>
                                              </div>
                                            </div>
                                            
                                            {/* Дополнительная информация */}
                                            <div className="space-y-2">
                                              <h4 className="font-semibold text-lg text-gray-700 mb-3">ℹ️ Дополнительно</h4>
                                              <div className="space-y-1 text-sm">
                                                <p><strong>Описание:</strong> {item.description}</p>
                                                <p><strong>Маршрут:</strong> {item.route}</p>
                                                <p><strong>Создан:</strong> {new Date(item.created_at).toLocaleDateString('ru-RU')}</p>
                                              </div>
                                            </div>
                                          </div>
                                        </div>
                                        
                                        {/* Кнопки действий */}
                                        <div className="ml-6 flex flex-col space-y-2">
                                          <Button
                                            onClick={() => {
                                              setSelectedCargoForDetailView(item);
                                              setCargoDetailsModal(true);
                                            }}
                                            variant="outline"
                                            className="flex items-center"
                                          >
                                            <Eye className="mr-2 h-4 w-4" />
                                            Подробнее
                                          </Button>
                                          
                                          <Button
                                            onClick={() => {
                                              setSelectedCargoForDetailView(item);
                                              setQuickPlacementModal(true);
                                            }}
                                            className="bg-green-600 hover:bg-green-700 text-white flex items-center"
                                          >
                                            <Grid3X3 className="mr-2 h-4 w-4" />
                                            Разместить
                                          </Button>
                                        </div>
                                      </div>
                                    </CardContent>
                                  </Card>
                                ))}
                              </div>
                            )}
                          </div>
                        </CardContent>
                        
                        {/* Пагинация для размещения грузов */}
                        {availableCargoForPlacement.length > 0 && availableCargoPagination && (
                          <DataPagination
                            pagination={availableCargoPagination}
                            onPageChange={handleAvailableCargoPageChange}
                            onPerPageChange={handleAvailableCargoPerPageChange}
                          />
                        )}
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
                              <TableHead>Номер</TableHead>
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
                                <TableCell>
                                  <Badge variant="secondary" className="text-xs">
                                    {u.user_number || 'N/A'}
                                  </Badge>
                                </TableCell>
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
                                      onClick={() => openAdminEditUser(u)}
                                      className="text-orange-600 hover:text-orange-700"
                                      title="Редактировать профиль пользователя"
                                    >
                                      <Edit className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => fetchUserProfile(u.id)}
                                      className="text-blue-600 hover:text-blue-700"
                                      title="Просмотр профиля и истории"
                                    >
                                      <Eye className="h-4 w-4" />
                                    </Button>
                                    {user.role === 'warehouse_operator' && (
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => openQuickCargoModal(u)}
                                        className="text-green-600 hover:text-green-700"
                                        title="Быстрое создание груза"
                                      >
                                        <Plus className="h-4 w-4" />
                                      </Button>
                                    )}
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => openRoleModal(u)}
                                      className="text-blue-600 hover:text-blue-700"
                                      title="Изменить роль"
                                    >
                                      <Shield className="h-4 w-4" />
                                    </Button>
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
                        <CardDescription>Операторы складов с детальной информацией и управлением ролями</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Номер</TableHead>
                              <TableHead>ФИО</TableHead>
                              <TableHead>Телефон</TableHead>
                              <TableHead>Дата регистрации</TableHead>
                              <TableHead>Статус</TableHead>
                              <TableHead>Роль</TableHead>
                              <TableHead>Действия</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {usersByRole.warehouse_operator.map((u) => (
                              <TableRow key={u.id}>
                                <TableCell>
                                  <Badge variant="secondary" className="text-xs">
                                    {u.user_number || 'N/A'}
                                  </Badge>
                                </TableCell>
                                <TableCell className="font-medium">{u.full_name}</TableCell>
                                <TableCell>{u.phone}</TableCell>
                                <TableCell>{new Date(u.created_at).toLocaleDateString('ru-RU')}</TableCell>
                                <TableCell>
                                  <Badge variant={u.is_active ? 'default' : 'secondary'}>
                                    {u.is_active ? 'Активен' : 'Заблокирован'}
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline" className="bg-orange-50 text-orange-700">
                                    Оператор склада
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  <div className="flex space-x-2">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => fetchOperatorProfile(u.id)}
                                      className="text-blue-600 hover:text-blue-700"
                                      title="Просмотр профиля и статистики"
                                    >
                                      <Eye className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => {
                                        setSelectedUserForRole(u);
                                        setNewRole('admin');
                                        setShowRoleModal(true);
                                      }}
                                      className="text-purple-600 hover:text-purple-700"
                                      title="Повысить до администратора"
                                    >
                                      <ArrowUp className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => toggleUserStatus(u.id, u.is_active)}
                                      className={u.is_active ? "text-red-600 hover:text-red-700" : "text-green-600 hover:text-green-700"}
                                      title={u.is_active ? "Заблокировать" : "Разблокировать"}
                                    >
                                      {u.is_active ? <Ban className="h-4 w-4" /> : <CheckCircle className="h-4 w-4" />}
                                    </Button>
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>

                        {usersByRole.warehouse_operator.length === 0 && (
                          <div className="text-center py-8">
                            <Warehouse className="mx-auto h-12 w-12 text-gray-400" />
                            <h3 className="mt-4 text-sm font-medium text-gray-900">Операторы не найдены</h3>
                            <p className="mt-1 text-sm text-gray-500">
                              Назначьте роль "Оператор склада" пользователям
                            </p>
                          </div>
                        )}
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

                  {/* Создание оператора склада (Функция 2) */}
                  {activeTab === 'users-create-operator' && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Plus className="mr-2 h-5 w-5" />
                          Создать нового оператора склада
                        </CardTitle>
                        <CardDescription>
                          Создание оператора с автоматической привязкой к складу
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleCreateOperator} className="space-y-4 max-w-md">
                          <div>
                            <Label htmlFor="operator-full-name">ФИО оператора</Label>
                            <Input
                              id="operator-full-name"
                              value={operatorCreateForm.full_name}
                              onChange={(e) => setOperatorCreateForm({...operatorCreateForm, full_name: e.target.value})}
                              placeholder="Иванов Иван Иванович"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="operator-phone">Телефон</Label>
                            <Input
                              id="operator-phone"
                              type="tel"
                              value={operatorCreateForm.phone}
                              onChange={(e) => setOperatorCreateForm({...operatorCreateForm, phone: e.target.value})}
                              placeholder="+79XXXXXXXXX"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="operator-address">Адрес проживания</Label>
                            <Input
                              id="operator-address"
                              value={operatorCreateForm.address}
                              onChange={(e) => setOperatorCreateForm({...operatorCreateForm, address: e.target.value})}
                              placeholder="Москва, ул. Примерная, 10, кв. 5"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="operator-password">Пароль</Label>
                            <Input
                              id="operator-password"
                              type="password"
                              value={operatorCreateForm.password}
                              onChange={(e) => setOperatorCreateForm({...operatorCreateForm, password: e.target.value})}
                              placeholder="Минимум 6 символов"
                              minLength={6}
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="operator-warehouse">Назначить на склад</Label>
                            <Select 
                              value={operatorCreateForm.warehouse_id} 
                              onValueChange={(value) => setOperatorCreateForm({...operatorCreateForm, warehouse_id: value})}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Выберите склад" />
                              </SelectTrigger>
                              <SelectContent>
                                {warehouses.map((warehouse) => (
                                  <SelectItem key={warehouse.id} value={warehouse.id}>
                                    {warehouse.name} - {warehouse.location}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <Button type="submit" className="w-full">
                            <Plus className="mr-2 h-4 w-4" />
                            Создать оператора
                          </Button>
                        </form>

                        {/* Список созданных операторов */}
                        <div className="mt-8">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold">Созданные операторы</h3>
                            <div className="flex space-x-2">
                              <Button 
                                variant="destructive"
                                size="sm"
                                onClick={handleCleanupTestData}
                                className="bg-red-600 hover:bg-red-700"
                              >
                                🧹 Очистить тестовые данные
                              </Button>
                              <Button 
                                variant="outline" 
                                onClick={fetchAllOperators}
                              >
                                Обновить список
                              </Button>
                            </div>
                          </div>
                          {allOperators.length === 0 ? (
                            <div className="text-center py-8">
                              <Users className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Операторы не созданы</p>
                            </div>
                          ) : (
                            <div className="space-y-4">
                              {allOperators.map((operator) => (
                                <div key={operator.id} className="border rounded-lg p-4">
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <h4 className="font-semibold">{operator.full_name}</h4>
                                      <p className="text-sm text-gray-600">{operator.phone}</p>
                                      <p className="text-sm text-gray-600">{operator.address}</p>
                                      <div className="flex items-center mt-2">
                                        <Badge variant="outline" className="mr-2">
                                          {operator.role}
                                        </Badge>
                                        <span className="text-xs text-gray-500">
                                          Создан: {new Date(operator.created_at).toLocaleDateString('ru-RU')}
                                        </span>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <p className="text-sm font-medium">Склады ({operator.warehouses_count})</p>
                                      {operator.warehouses && operator.warehouses.length > 0 ? (
                                        <div className="text-xs text-gray-600">
                                          {operator.warehouses.map((warehouse) => (
                                            <div key={warehouse.id}>
                                              {warehouse.name}
                                            </div>
                                          ))}
                                        </div>
                                      ) : (
                                        <span className="text-xs text-red-600">Нет складов</span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
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
                  {/* НОВЫЕ ЗАКАЗЫ ОТ КЛИЕНТОВ */}
                  {(activeTab === 'notifications-client-orders' || !activeTab || activeTab === 'notifications-management') && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between">
                          <div className="flex items-center">
                            <ShoppingCart className="mr-2 h-5 w-5 text-orange-600" />
                            Новые заказы от клиентов ({newOrdersCount})
                          </div>
                          <div className="space-x-2">
                            <Button onClick={fetchNewOrdersCount} variant="outline" size="sm">
                              <RefreshCw className="w-4 h-4 mr-1" />
                              Обновить
                            </Button>
                          </div>
                        </CardTitle>
                        <CardDescription>
                          Заказы от клиентов через форму онлайн-заказа с возможностью редактирования
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {pendingOrders.length === 0 ? (
                            <div className="text-center py-8">
                              <ShoppingCart className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                              <p className="text-gray-500">Новых заказов от клиентов нет</p>
                            </div>
                          ) : (
                            pendingOrders.map((order) => (
                              <div key={order.id} className="border rounded-lg p-6 bg-orange-50 hover:bg-orange-100 transition-colors">
                                <div className="flex justify-between items-start mb-4">
                                  <div>
                                    <h3 className="text-lg font-semibold text-orange-800">
                                      Заказ №{order.request_number}
                                    </h3>
                                    <p className="text-sm text-gray-600">
                                      Создан: {new Date(order.created_at).toLocaleDateString('ru-RU')} {new Date(order.created_at).toLocaleTimeString('ru-RU')}
                                    </p>
                                  </div>
                                  <div className="flex flex-col items-end space-y-2">
                                    <Badge variant="destructive" className="bg-orange-100 text-orange-800 border-orange-200">
                                      Новый заказ
                                    </Badge>
                                    {order.admin_notes && (
                                      <Badge variant="outline" className="text-blue-600 border-blue-200">
                                        Есть заметки
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                                  <div className="space-y-3">
                                    <h4 className="font-medium text-gray-900 flex items-center">
                                      <User className="w-4 h-4 mr-1" />
                                      Отправитель
                                    </h4>
                                    <div className="text-sm text-gray-600 space-y-1 pl-5">
                                      <p><strong>ФИО:</strong> {order.sender_full_name}</p>
                                      <p><strong>Телефон:</strong> {order.sender_phone}</p>
                                      <p><strong>Адрес забора:</strong> {order.pickup_address}</p>
                                    </div>
                                  </div>
                                  
                                  <div className="space-y-3">
                                    <h4 className="font-medium text-gray-900 flex items-center">
                                      <MapPin className="w-4 h-4 mr-1" />
                                      Получатель
                                    </h4>
                                    <div className="text-sm text-gray-600 space-y-1 pl-5">
                                      <p><strong>ФИО:</strong> {order.recipient_full_name}</p>
                                      <p><strong>Телефон:</strong> {order.recipient_phone}</p>
                                      <p><strong>Адрес доставки:</strong> {order.recipient_address}</p>
                                    </div>
                                  </div>
                                </div>

                                <div className="mb-4 p-4 bg-white/50 rounded-lg">
                                  <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                                    <Package className="w-4 h-4 mr-1" />
                                    Информация о грузе
                                  </h4>
                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                                    <div>
                                      <p><strong>Название:</strong> {order.cargo_name}</p>
                                      <p><strong>Описание:</strong> {order.description}</p>
                                    </div>
                                    <div>
                                      <p><strong>Вес:</strong> {order.weight} кг</p>
                                      <p><strong>Стоимость:</strong> {order.declared_value} ₽</p>
                                    </div>
                                    <div>
                                      <p><strong>Маршрут:</strong> {order.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}</p>
                                    </div>
                                  </div>
                                </div>

                                {order.admin_notes && (
                                  <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                                    <p className="text-sm text-blue-800">
                                      <strong>Заметки администратора:</strong> {order.admin_notes}
                                    </p>
                                  </div>
                                )}

                                <div className="flex flex-wrap gap-2 pt-4 border-t border-orange-200">
                                  <Button 
                                    onClick={() => handleOrderDetailsView(order)}
                                    variant="outline" 
                                    size="sm"
                                    className="flex items-center"
                                  >
                                    <Eye className="w-4 h-4 mr-1" />
                                    Просмотреть
                                  </Button>
                                  <Button 
                                    onClick={() => handleOrderEdit(order)}
                                    variant="outline" 
                                    size="sm"
                                    className="flex items-center text-blue-600 border-blue-200 hover:bg-blue-50"
                                  >
                                    <Edit className="w-4 h-4 mr-1" />
                                    Редактировать
                                  </Button>
                                  <Button 
                                    onClick={() => handleAcceptOrder(order.id)}
                                    size="sm"
                                    className="flex items-center bg-green-600 hover:bg-green-700"
                                  >
                                    <CheckCircle className="w-4 h-4 mr-1" />
                                    Принять заказ
                                  </Button>
                                  <Button 
                                    onClick={() => handleRejectOrder(order.id, 'Заказ отклонен администратором')}
                                    variant="destructive" 
                                    size="sm"
                                    className="flex items-center"
                                  >
                                    <XCircle className="w-4 h-4 mr-1" />
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
          
          {warehouseLayout ? (
            <div className="space-y-4">
              {/* Статистика склада */}
              <div className="grid grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded">
                  <div className="text-2xl font-bold text-blue-600">{warehouseLayout.total_cells}</div>
                  <div className="text-sm">Всего ячеек</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded">
                  <div className="text-2xl font-bold text-red-600">{warehouseLayout.occupied_cells}</div>
                  <div className="text-sm">Занято</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded">
                  <div className="text-2xl font-bold text-green-600">{warehouseLayout.total_cells - warehouseLayout.occupied_cells}</div>
                  <div className="text-sm">Свободно</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-gray-600">{warehouseLayout.occupancy_percentage}%</div>
                  <div className="text-sm">Заполненность</div>
                </div>
              </div>

              {/* Схема склада с информацией о грузах */}
              <div className="max-h-96 overflow-auto border rounded-lg p-4">
                <div className="space-y-6">
                  {warehouseLayout.layout && Object.entries(warehouseLayout.layout).map(([blockKey, block]) => (
                    <div key={blockKey} className="border rounded-lg p-4">
                      <h3 className="font-bold mb-3 text-center bg-gray-100 p-2 rounded">
                        Блок {block.block_number}
                      </h3>
                      <div className="space-y-4">
                        {block.shelves && Object.entries(block.shelves).map(([shelfKey, shelf]) => (
                          <div key={shelfKey}>
                            <h4 className="font-semibold mb-2 text-sm bg-gray-50 p-1 rounded">
                              Полка {shelf.shelf_number}
                            </h4>
                            <div className="grid grid-cols-5 gap-2">
                              {shelf.cells && Object.entries(shelf.cells).slice(0, 10).map(([cellKey, cell]) => (
                                <div
                                  key={cellKey}
                                  className={`p-2 text-xs text-center rounded border-2 transition-all cursor-pointer hover:scale-105 ${
                                    cell.is_occupied 
                                      ? 'bg-red-100 border-red-300 text-red-800 hover:bg-red-200' 
                                      : 'bg-green-100 border-green-300 text-green-800 hover:bg-green-200'
                                  }`}
                                  title={cell.cargo ? `${cell.cargo.cargo_number} - ${cell.cargo.sender_full_name}` : 'Свободная ячейка'}
                                  onClick={() => {
                                    if (cell.is_occupied && cell.cargo) {
                                      setSelectedCargoForWarehouse(cell.cargo);
                                      setCargoDetailsModal(true);
                                    } else {
                                      showAlert('Ячейка свободна', 'info');
                                    }
                                  }}
                                >
                                  <div className="font-bold">Я{cell.cell_number}</div>
                                  {cell.cargo && (
                                    <div className="mt-1">
                                      <div className="font-semibold text-[9px]">{cell.cargo.cargo_number}</div>
                                      <div className="text-[8px]">{cell.cargo.weight}кг</div>
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
          ) : (
            <div className="text-center py-8">
              <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4">Загрузка схемы склада...</p>
              <p className="text-sm text-gray-400">
                Если схема не загружается, проверьте подключение или обратитесь к администратору.
              </p>
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

      {/* НОВЫЕ МОДАЛЫ ДЛЯ УПРАВЛЕНИЯ ЗАКАЗАМИ КЛИЕНТОВ */}

      {/* Модальное окно детального просмотра заказа клиента */}
      <Dialog open={orderDetailsModal} onOpenChange={setOrderDetailsModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <ShoppingCart className="w-5 h-5 mr-2 text-orange-600" />
              Детали заказа №{selectedOrder?.request_number}
            </DialogTitle>
            <DialogDescription>
              Просмотр полной информации о заказе клиента
            </DialogDescription>
          </DialogHeader>
          
          {selectedOrder && (
            <div className="space-y-6">
              {/* Основная информация */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600"><strong>Номер заказа:</strong></p>
                  <p className="font-medium">{selectedOrder.request_number}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600"><strong>Дата создания:</strong></p>
                  <p className="font-medium">
                    {new Date(selectedOrder.created_at).toLocaleDateString('ru-RU')} {' '}
                    {new Date(selectedOrder.created_at).toLocaleTimeString('ru-RU')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600"><strong>Статус:</strong></p>
                  <Badge variant={selectedOrder.status === 'pending' ? 'destructive' : 'default'}>
                    {selectedOrder.status === 'pending' ? 'Ожидает обработки' : selectedOrder.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-600"><strong>Маршрут:</strong></p>
                  <p className="font-medium">
                    {selectedOrder.route === 'moscow_to_tajikistan' ? 'Москва → Таджикистан' : 'Таджикистан → Москва'}
                  </p>
                </div>
              </div>

              {/* Информация об отправителе */}
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-3 flex items-center">
                  <User className="w-5 h-5 mr-2 text-blue-600" />
                  Отправитель
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600"><strong>ФИО:</strong></p>
                    <p className="font-medium">{selectedOrder.sender_full_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Телефон:</strong></p>
                    <p className="font-medium">{selectedOrder.sender_phone}</p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-sm text-gray-600"><strong>Адрес забора:</strong></p>
                    <p className="font-medium">{selectedOrder.pickup_address}</p>
                  </div>
                </div>
              </div>

              {/* Информация о получателе */}
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-3 flex items-center">
                  <MapPin className="w-5 h-5 mr-2 text-green-600" />
                  Получатель
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600"><strong>ФИО:</strong></p>
                    <p className="font-medium">{selectedOrder.recipient_full_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Телефон:</strong></p>
                    <p className="font-medium">{selectedOrder.recipient_phone}</p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-sm text-gray-600"><strong>Адрес доставки:</strong></p>
                    <p className="font-medium">{selectedOrder.recipient_address}</p>
                  </div>
                </div>
              </div>

              {/* Информация о грузе */}
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-3 flex items-center">
                  <Package className="w-5 h-5 mr-2 text-purple-600" />
                  Информация о грузе
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600"><strong>Название груза:</strong></p>
                    <p className="font-medium">{selectedOrder.cargo_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Вес:</strong></p>
                    <p className="font-medium">{selectedOrder.weight} кг</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Объявленная стоимость:</strong></p>
                    <p className="font-medium">{selectedOrder.declared_value} ₽</p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-sm text-gray-600"><strong>Описание:</strong></p>
                    <p className="font-medium">{selectedOrder.description}</p>
                  </div>
                </div>
              </div>

              {/* Заметки администратора */}
              {selectedOrder.admin_notes && (
                <div className="border rounded-lg p-4 bg-blue-50">
                  <h3 className="font-semibold text-lg mb-3 flex items-center">
                    <FileText className="w-5 h-5 mr-2 text-blue-600" />
                    Заметки администратора
                  </h3>
                  <p className="text-gray-700">{selectedOrder.admin_notes}</p>
                </div>
              )}

              {/* Действия */}
              <div className="flex justify-between items-center pt-4 border-t">
                <div className="space-x-2">
                  <Button 
                    onClick={() => {
                      handleOrderEdit(selectedOrder);
                      setOrderDetailsModal(false);
                    }}
                    variant="outline"
                    className="flex items-center"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Редактировать
                  </Button>
                </div>
                <div className="space-x-2">
                  <Button 
                    onClick={() => handleAcceptOrder(selectedOrder.id)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Принять заказ
                  </Button>
                  <Button 
                    onClick={() => handleRejectOrder(selectedOrder.id, 'Заказ отклонен администратором')}
                    variant="destructive"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Отклонить
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Модальное окно редактирования заказа клиента */}
      <Dialog open={editOrderModal} onOpenChange={setEditOrderModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Edit className="w-5 h-5 mr-2 text-blue-600" />
              Редактирование заказа №{selectedOrder?.request_number}
            </DialogTitle>
            <DialogDescription>
              Изменение информации о получателе, отправителе и грузе
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={(e) => { e.preventDefault(); handleSaveOrderChanges(); }}>
            <div className="space-y-6">
              {/* Информация об отправителе */}
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-4 flex items-center">
                  <User className="w-5 h-5 mr-2 text-blue-600" />
                  Отправитель
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="sender_full_name">ФИО отправителя</Label>
                    <Input
                      id="sender_full_name"
                      value={orderEditForm.sender_full_name}
                      onChange={(e) => setOrderEditForm({...orderEditForm, sender_full_name: e.target.value})}
                      placeholder="Иван Иванович Петров"
                    />
                  </div>
                  <div>
                    <Label htmlFor="sender_phone">Телефон отправителя</Label>
                    <Input
                      id="sender_phone"
                      value={orderEditForm.sender_phone}
                      onChange={(e) => setOrderEditForm({...orderEditForm, sender_phone: e.target.value})}
                      placeholder="+7 900 123-45-67"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor="pickup_address">Адрес забора</Label>
                    <Input
                      id="pickup_address"
                      value={orderEditForm.pickup_address}
                      onChange={(e) => setOrderEditForm({...orderEditForm, pickup_address: e.target.value})}
                      placeholder="г. Москва, ул. Тверская, д. 1"
                    />
                  </div>
                </div>
              </div>

              {/* Информация о получателе */}
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-4 flex items-center">
                  <MapPin className="w-5 h-5 mr-2 text-green-600" />
                  Получатель
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="recipient_full_name">ФИО получателя</Label>
                    <Input
                      id="recipient_full_name"
                      value={orderEditForm.recipient_full_name}
                      onChange={(e) => setOrderEditForm({...orderEditForm, recipient_full_name: e.target.value})}
                      placeholder="Петр Петрович Иванов"
                    />
                  </div>
                  <div>
                    <Label htmlFor="recipient_phone">Телефон получателя</Label>
                    <Input
                      id="recipient_phone"
                      value={orderEditForm.recipient_phone}
                      onChange={(e) => setOrderEditForm({...orderEditForm, recipient_phone: e.target.value})}
                      placeholder="+992 900 123456"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor="recipient_address">Адрес доставки</Label>
                    <Input
                      id="recipient_address"
                      value={orderEditForm.recipient_address}
                      onChange={(e) => setOrderEditForm({...orderEditForm, recipient_address: e.target.value})}
                      placeholder="г. Душанбе, ул. Рудаки, д. 10"
                    />
                  </div>
                </div>
              </div>

              {/* Информация о грузе */}
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-lg mb-4 flex items-center">
                  <Package className="w-5 h-5 mr-2 text-purple-600" />
                  Груз
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="cargo_name">Название груза</Label>
                    <Input
                      id="cargo_name"
                      value={orderEditForm.cargo_name}
                      onChange={(e) => setOrderEditForm({...orderEditForm, cargo_name: e.target.value})}
                      placeholder="Документы"
                    />
                  </div>
                  <div>
                    <Label htmlFor="route">Маршрут</Label>
                    <Select value={orderEditForm.route} onValueChange={(value) => setOrderEditForm({...orderEditForm, route: value})}>
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите маршрут" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="moscow_to_tajikistan">Москва → Таджикистан</SelectItem>
                        <SelectItem value="tajikistan_to_moscow">Таджикистан → Москва</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="weight">Вес (кг)</Label>
                    <Input
                      id="weight"
                      type="number"
                      value={orderEditForm.weight}
                      onChange={(e) => setOrderEditForm({...orderEditForm, weight: e.target.value})}
                      placeholder="1.5"
                      step="0.1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="declared_value">Объявленная стоимость (₽)</Label>
                    <Input
                      id="declared_value"
                      type="number"
                      value={orderEditForm.declared_value}
                      onChange={(e) => setOrderEditForm({...orderEditForm, declared_value: e.target.value})}
                      placeholder="10000"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor="description">Описание груза</Label>
                    <Textarea
                      id="description"
                      value={orderEditForm.description}
                      onChange={(e) => setOrderEditForm({...orderEditForm, description: e.target.value})}
                      placeholder="Подробное описание груза"
                      rows={3}
                    />
                  </div>
                </div>
              </div>

              {/* Заметки администратора */}
              <div className="border rounded-lg p-4 bg-blue-50">
                <h3 className="font-semibold text-lg mb-4 flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-blue-600" />
                  Заметки администратора
                </h3>
                <Textarea
                  value={orderEditForm.admin_notes}
                  onChange={(e) => setOrderEditForm({...orderEditForm, admin_notes: e.target.value})}
                  placeholder="Добавьте заметки по обработке заказа..."
                  rows={3}
                />
              </div>

              {/* Кнопки действий */}
              <div className="flex justify-between items-center pt-4 border-t">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => {
                    setEditOrderModal(false);
                    setOrderEditForm({
                      sender_full_name: '',
                      sender_phone: '',
                      recipient_full_name: '',
                      recipient_phone: '',
                      recipient_address: '',
                      pickup_address: '',
                      cargo_name: '',
                      weight: '',
                      declared_value: '',
                      description: '',
                      route: '',
                      admin_notes: ''
                    });
                  }}
                >
                  Отмена
                </Button>
                <div className="space-x-2">
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                    <Save className="w-4 h-4 mr-2" />
                    Сохранить изменения
                  </Button>
                </div>
              </div>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* МОДАЛЬНЫЕ ОКНА ДЛЯ УПРАВЛЕНИЯ РАЗМЕЩЕНИЕМ ГРУЗОВ */}

      {/* Модальное окно детального просмотра груза */}
      <Dialog open={cargoDetailsModal} onOpenChange={setCargoDetailsModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Package className="w-5 h-5 mr-2 text-blue-600" />
              Подробная информация о грузе №{selectedCargoForDetailView?.cargo_number}
            </DialogTitle>
            <DialogDescription>
              Полная информация о грузе, отправителе, получателе и операторе
            </DialogDescription>
          </DialogHeader>
          
          {selectedCargoForDetailView && (
            <div className="space-y-6">
              {/* Информация о грузе */}
              <div className="p-4 bg-blue-50 rounded-lg">
                <h3 className="font-bold text-lg text-blue-700 mb-3">📦 Информация о грузе</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600"><strong>Номер груза:</strong></p>
                    <p className="font-medium text-lg">{selectedCargoForDetailView.cargo_number}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Наименование:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.cargo_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Вес:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.weight} кг</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Объявленная стоимость:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.declared_value} ₽</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-600"><strong>Описание:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.description}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Маршрут:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.route}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Статус обработки:</strong></p>
                    <Badge variant={getProcessingStatusBadgeVariant(selectedCargoForDetailView.processing_status)}>
                      {getProcessingStatusLabel(selectedCargoForDetailView.processing_status)}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Информация об отправителе */}
              <div className="p-4 bg-green-50 rounded-lg">
                <h3 className="font-bold text-lg text-green-700 mb-3">👤 Отправитель</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600"><strong>Полное имя:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.sender_full_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Телефон:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.sender_phone}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-600"><strong>Адрес отправления:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.sender_address}</p>
                  </div>
                </div>
              </div>

              {/* Информация о получателе */}
              <div className="p-4 bg-yellow-50 rounded-lg">
                <h3 className="font-bold text-lg text-yellow-700 mb-3">📍 Получатель</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600"><strong>Полное имя:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.recipient_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Телефон:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.recipient_phone}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-600"><strong>Адрес доставки:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.recipient_address}</p>
                  </div>
                </div>
              </div>

              {/* Информация об операторе */}
              <div className="p-4 bg-purple-50 rounded-lg">
                <h3 className="font-bold text-lg text-purple-700 mb-3">👨‍💼 Оператор</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600"><strong>Оператор, принявший груз:</strong></p>
                    <p className="font-medium">{selectedCargoForDetailView.accepting_operator}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600"><strong>Дата приема:</strong></p>
                    <p className="font-medium">
                      {new Date(selectedCargoForDetailView.created_at).toLocaleDateString('ru-RU')} {' '}
                      {new Date(selectedCargoForDetailView.created_at).toLocaleTimeString('ru-RU')}
                    </p>
                  </div>
                  {selectedCargoForDetailView.warehouse_location && (
                    <>
                      <div>
                        <p className="text-sm text-gray-600"><strong>Размещение:</strong></p>
                        <p className="font-medium text-blue-600">{selectedCargoForDetailView.warehouse_location}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600"><strong>Размещен оператором:</strong></p>
                        <p className="font-medium">{selectedCargoForDetailView.placed_by_operator || 'Не размещен'}</p>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Кнопки действий */}
              <div className="flex justify-end space-x-4">
                <Button variant="outline" onClick={() => setCargoDetailsModal(false)}>
                  Закрыть
                </Button>
                {(selectedCargoForDetailView.processing_status === 'paid' || selectedCargoForDetailView.processing_status === 'invoice_printed') && !selectedCargoForDetailView.warehouse_location && (
                  <Button
                    onClick={() => {
                      setCargoDetailsModal(false);
                      setCargoMoveModal(true);
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    <Grid3X3 className="mr-2 h-4 w-4" />
                    Переместить груз
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Модальное окно перемещения груза */}
      <Dialog open={cargoMoveModal} onOpenChange={setCargoMoveModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Grid3X3 className="w-5 h-5 mr-2 text-blue-600" />
              Переместить груз
            </DialogTitle>
            <DialogDescription>
              Груз №{selectedCargoForWarehouse?.cargo_number}
              <br />
              Текущее местоположение: {selectedCargoForWarehouse?.warehouse_location}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Информация о грузе */}
            {selectedCargoForWarehouse && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="font-medium text-lg">{selectedCargoForWarehouse.cargo_number}</p>
                <p className="text-sm text-gray-600">{selectedCargoForWarehouse.cargo_name}</p>
                <p className="text-sm text-gray-600">Вес: {selectedCargoForWarehouse.weight} кг</p>
              </div>
            )}

            {/* Форма перемещения */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Новый блок</Label>
                <Input
                  type="number"
                  min="1"
                  max="9"
                  value={cargoMoveForm.to_block}
                  onChange={(e) => setCargoMoveForm({
                    ...cargoMoveForm,
                    to_block: parseInt(e.target.value) || 1
                  })}
                />
              </div>
              <div>
                <Label>Новая полка</Label>
                <Input
                  type="number"
                  min="1"
                  max="3"
                  value={cargoMoveForm.to_shelf}
                  onChange={(e) => setCargoMoveForm({
                    ...cargoMoveForm,
                    to_shelf: parseInt(e.target.value) || 1
                  })}
                />
              </div>
              <div>
                <Label>Новая ячейка</Label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={cargoMoveForm.to_cell}
                  onChange={(e) => setCargoMoveForm({
                    ...cargoMoveForm,
                    to_cell: parseInt(e.target.value) || 1
                  })}
                />
              </div>
            </div>

            <div className="p-2 bg-blue-50 rounded text-sm text-blue-700">
              <strong>Новое местоположение:</strong> Б{cargoMoveForm.to_block}-П{cargoMoveForm.to_shelf}-Я{cargoMoveForm.to_cell}
            </div>

            {/* Кнопки */}
            <div className="flex justify-end space-x-4 pt-4">
              <Button variant="outline" onClick={() => {
                setCargoMoveModal(false);
                setCargoMoveForm({
                  to_block: 1,
                  to_shelf: 1,
                  to_cell: 1
                });
              }}>
                Отмена
              </Button>
              <Button
                onClick={handleCargoMove}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                <Grid3X3 className="mr-2 h-4 w-4" />
                Переместить
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно изменения роли пользователя */}
      <Dialog open={showRoleModal} onOpenChange={setShowRoleModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Изменение роли пользователя</DialogTitle>
            <DialogDescription>
              Изменение роли пользователя {selectedUserForRole?.full_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {selectedUserForRole && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm">
                  <p><strong>Номер:</strong> {selectedUserForRole.user_number || 'N/A'}</p>
                  <p><strong>ФИО:</strong> {selectedUserForRole.full_name}</p>
                  <p><strong>Телефон:</strong> {selectedUserForRole.phone}</p>
                  <p><strong>Текущая роль:</strong> {getRoleLabel(selectedUserForRole.role)}</p>
                </div>
              </div>
            )}
            
            <div>
              <Label htmlFor="role-select">Новая роль</Label>
              <Select value={newRole} onValueChange={setNewRole}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите роль" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Пользователь</SelectItem>
                  <SelectItem value="warehouse_operator">Оператор склада</SelectItem>
                  <SelectItem value="admin">Администратор</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2 mt-6">
            <Button 
              variant="outline" 
              onClick={() => {
                setShowRoleModal(false);
                setSelectedUserForRole(null);
                setNewRole('');
              }}
            >
              Отмена
            </Button>
            <Button 
              onClick={handleRoleChange}
              disabled={!newRole || newRole === selectedUserForRole?.role}
            >
              Изменить роль
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно профиля оператора */}
      <Dialog open={showOperatorProfile} onOpenChange={setShowOperatorProfile}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Профиль оператора склада</DialogTitle>
            <DialogDescription>
              Детальная информация о работе оператора и статистика
            </DialogDescription>
          </DialogHeader>
          
          {profileLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Загрузка профиля...</p>
            </div>
          ) : selectedOperatorProfile && (
            <div className="space-y-6">
              {/* Информация об операторе */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-semibold text-lg mb-3">Информация об операторе</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Номер</label>
                    <p className="text-lg">{selectedOperatorProfile.user_info.user_number}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">ФИО</label>
                    <p className="text-lg">{selectedOperatorProfile.user_info.full_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Телефон</label>
                    <p className="text-lg">{selectedOperatorProfile.user_info.phone}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Статус</label>
                    <Badge variant={selectedOperatorProfile.user_info.is_active ? 'default' : 'secondary'}>
                      {selectedOperatorProfile.user_info.is_active ? 'Активен' : 'Заблокирован'}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Статистика работы */}
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="font-semibold text-lg mb-3">Статистика работы</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedOperatorProfile.work_statistics.total_cargo_accepted}
                    </div>
                    <div className="text-sm text-gray-600">Всего грузов</div>
                  </div>
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {selectedOperatorProfile.work_statistics.recent_cargo_count}
                    </div>
                    <div className="text-sm text-gray-600">За 30 дней</div>
                  </div>
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {selectedOperatorProfile.work_statistics.avg_cargo_per_day}
                    </div>
                    <div className="text-sm text-gray-600">В день (средн.)</div>
                  </div>
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {selectedOperatorProfile.associated_warehouses.length}
                    </div>
                    <div className="text-sm text-gray-600">Складов</div>
                  </div>
                </div>
              </div>

              {/* Связанные склады */}
              {selectedOperatorProfile.associated_warehouses.length > 0 && (
                <div>
                  <h3 className="font-semibold text-lg mb-3">Связанные склады</h3>
                  <div className="space-y-2">
                    {selectedOperatorProfile.associated_warehouses.map((warehouse, index) => (
                      <div key={index} className="bg-white border rounded-lg p-3">
                        <div className="flex justify-between items-center">
                          <div>
                            <h4 className="font-medium">{warehouse.name}</h4>
                            <p className="text-sm text-gray-600">{warehouse.location}</p>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium">{warehouse.cargo_count} грузов</div>
                            <div className="text-xs text-gray-500">
                              {warehouse.binding_date && new Date(warehouse.binding_date).toLocaleDateString('ru-RU')}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Последняя активность */}
              {selectedOperatorProfile.recent_activity.length > 0 && (
                <div>
                  <h3 className="font-semibold text-lg mb-3">Последняя активность</h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {selectedOperatorProfile.recent_activity.map((activity, index) => (
                      <div key={index} className="bg-white border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-medium">{activity.cargo_number}</h4>
                            <p className="text-sm text-gray-600">{activity.cargo_name}</p>
                            <p className="text-sm text-gray-500">От: {activity.sender_full_name}</p>
                          </div>
                          <div className="text-right">
                            <Badge variant="outline">{activity.processing_status}</Badge>
                            <div className="text-xs text-gray-500 mt-1">
                              {new Date(activity.created_at).toLocaleDateString('ru-RU')}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Модальное окно профиля пользователя */}
      <Dialog open={showUserProfile} onOpenChange={setShowUserProfile}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Профиль пользователя</DialogTitle>
            <DialogDescription>
              Детальная информация о пользователе и история отправлений
            </DialogDescription>
          </DialogHeader>
          
          {profileLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Загрузка профиля...</p>
            </div>
          ) : selectedUserProfile && (
            <div className="space-y-6">
              {/* Информация о пользователе */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-semibold text-lg">Информация о пользователе</h3>
                  {(user.role === 'warehouse_operator' || user.role === 'admin') && (
                    <Button
                      size="sm"
                      onClick={() => openQuickCargoFromProfile(selectedUserProfile.user_info)}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Оформить грузы
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Номер</label>
                    <p className="text-lg">{selectedUserProfile.user_info.user_number}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">ФИО</label>
                    <p className="text-lg">{selectedUserProfile.user_info.full_name}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Телефон</label>
                    <p className="text-lg">{selectedUserProfile.user_info.phone}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Роль</label>
                    <Badge variant="outline">{getRoleLabel(selectedUserProfile.user_info.role)}</Badge>
                  </div>
                </div>
              </div>

              {/* Статистика отправлений */}
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="font-semibold text-lg mb-3">Статистика отправлений</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedUserProfile.shipping_statistics.total_sent_cargo}
                    </div>
                    <div className="text-sm text-gray-600">Отправлено</div>
                  </div>
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {selectedUserProfile.shipping_statistics.total_received_cargo}
                    </div>
                    <div className="text-sm text-gray-600">Получено</div>
                  </div>
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {selectedUserProfile.shipping_statistics.total_cargo_requests}
                    </div>
                    <div className="text-sm text-gray-600">Заявок</div>
                  </div>
                  <div className="bg-white p-3 rounded border text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {selectedUserProfile.frequent_recipients.length}
                    </div>
                    <div className="text-sm text-gray-600">Получателей</div>
                  </div>
                </div>
              </div>

              {/* Часто используемые получатели */}
              {selectedUserProfile.frequent_recipients.length > 0 && (
                <div>
                  <h3 className="font-semibold text-lg mb-3">Часто используемые получатели</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-48 overflow-y-auto">
                    {selectedUserProfile.frequent_recipients.slice(0, 6).map((recipient, index) => (
                      <div key={index} className="bg-white border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-medium">{recipient.recipient_full_name}</h4>
                            <p className="text-sm text-gray-600">{recipient.recipient_phone}</p>
                            <p className="text-xs text-gray-500">{recipient.recipient_address}</p>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium">{recipient.shipment_count} раз</div>
                            <div className="text-xs text-gray-500">
                              {recipient.last_sent && new Date(recipient.last_sent).toLocaleDateString('ru-RU')}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Последние отправления */}
              {selectedUserProfile.recent_shipments.length > 0 && (
                <div>
                  <h3 className="font-semibold text-lg mb-3">Последние отправления</h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {selectedUserProfile.recent_shipments.slice(0, 8).map((shipment, index) => (
                      <div key={index} className="bg-white border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-medium">{shipment.cargo_number} - {shipment.cargo_name}</h4>
                            <p className="text-sm text-gray-600">
                              {shipment.weight} кг • {shipment.declared_value} руб
                            </p>
                            <p className="text-sm text-gray-500">
                              Получатель: {shipment.recipient_full_name}
                            </p>
                          </div>
                          <div className="text-right">
                            <Badge variant="outline">{shipment.status}</Badge>
                            <div className="text-xs text-gray-500 mt-1">
                              {new Date(shipment.created_at).toLocaleDateString('ru-RU')}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Модальное окно быстрого создания груза */}
      <Dialog open={showQuickCargoModal} onOpenChange={setShowQuickCargoModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Быстрое создание груза</DialogTitle>
            <DialogDescription>
              Создание груза с автозаполнением из истории пользователя
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Выбор получателя из истории */}
            {frequentRecipients.length > 0 && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-semibold text-lg mb-3">Выберите получателя из истории</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-32 overflow-y-auto">
                  {frequentRecipients.slice(0, 6).map((recipient, index) => (
                    <button
                      key={index}
                      className={`p-2 text-left rounded border ${
                        selectedRecipient?.recipient_phone === recipient.recipient_phone
                          ? 'bg-blue-100 border-blue-300'
                          : 'bg-white hover:bg-gray-50'
                      }`}
                      onClick={() => selectRecipientFromHistory(recipient)}
                    >
                      <div className="font-medium text-sm">{recipient.recipient_full_name}</div>
                      <div className="text-xs text-gray-600">{recipient.recipient_phone}</div>
                      <div className="text-xs text-gray-500">{recipient.shipment_count} отправлений</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Данные получателя */}
            <div>
              <h3 className="font-semibold text-lg mb-3">Данные получателя</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <Label>ФИО получателя</Label>
                  <Input
                    value={quickCargoForm.recipient_data.recipient_full_name || ''}
                    onChange={(e) => setQuickCargoForm({
                      ...quickCargoForm,
                      recipient_data: {
                        ...quickCargoForm.recipient_data,
                        recipient_full_name: e.target.value
                      }
                    })}
                    required
                  />
                </div>
                <div>
                  <Label>Телефон получателя</Label>
                  <Input
                    value={quickCargoForm.recipient_data.recipient_phone || ''}
                    onChange={(e) => setQuickCargoForm({
                      ...quickCargoForm,
                      recipient_data: {
                        ...quickCargoForm.recipient_data,
                        recipient_phone: e.target.value
                      }
                    })}
                    required
                  />
                </div>
                <div>
                  <Label>Адрес получателя</Label>
                  <Input
                    value={quickCargoForm.recipient_data.recipient_address || ''}
                    onChange={(e) => setQuickCargoForm({
                      ...quickCargoForm,
                      recipient_data: {
                        ...quickCargoForm.recipient_data,
                        recipient_address: e.target.value
                      }
                    })}
                    required
                  />
                </div>
              </div>
            </div>

            {/* Грузы */}
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-semibold text-lg mb-3">Грузы</h3>
              {quickCargoForm.cargo_items.map((item, index) => (
                <div key={index} className="mb-4 p-3 bg-white rounded border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">Груз #{index + 1}</span>
                    {quickCargoForm.cargo_items.length > 1 && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => removeQuickCargoItem(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <Label>Название</Label>
                      <Input
                        value={item.cargo_name}
                        onChange={(e) => updateQuickCargoItem(index, 'cargo_name', e.target.value)}
                        placeholder="Документы, одежда..."
                        required
                      />
                    </div>
                    <div>
                      <Label>Вес (кг)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={item.weight}
                        onChange={(e) => updateQuickCargoItem(index, 'weight', e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <Label>Цена за кг (руб.)</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={item.price_per_kg}
                        onChange={(e) => updateQuickCargoItem(index, 'price_per_kg', e.target.value)}
                        required
                      />
                    </div>
                  </div>
                  
                  {item.weight && item.price_per_kg && (
                    <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                      Стоимость: {parseFloat(item.weight)} кг × {parseFloat(item.price_per_kg)} руб/кг = 
                      <span className="font-semibold text-green-600 ml-1">
                        {(parseFloat(item.weight) * parseFloat(item.price_per_kg)).toFixed(2)} руб
                      </span>
                    </div>
                  )}
                </div>
              ))}
              
              <Button
                type="button"
                variant="outline"
                onClick={addQuickCargoItem}
                className="w-full"
              >
                <Plus className="mr-2 h-4 w-4" />
                Добавить еще груз
              </Button>
            </div>

            {/* Итоги */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold text-lg mb-2">Итого</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-600">Общий вес:</span>
                  <div className="text-xl font-bold text-blue-600">
                    {calculateQuickCargoTotals().totalWeight.toFixed(1)} кг
                  </div>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Общая стоимость:</span>
                  <div className="text-xl font-bold text-green-600">
                    {calculateQuickCargoTotals().totalCost.toFixed(2)} руб
                  </div>
                </div>
              </div>
            </div>

            {/* Описание */}
            <div>
              <Label>Описание груза</Label>
              <textarea
                className="w-full p-2 border rounded-md"
                rows="3"
                value={quickCargoForm.description}
                onChange={(e) => setQuickCargoForm({...quickCargoForm, description: e.target.value})}
                placeholder="Дополнительная информация о грузе..."
                required
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button 
                variant="outline" 
                onClick={() => setShowQuickCargoModal(false)}
              >
                Отмена
              </Button>
              <Button 
                onClick={submitQuickCargo}
                disabled={
                  !quickCargoForm.recipient_data.recipient_full_name ||
                  !quickCargoForm.recipient_data.recipient_phone ||
                  !quickCargoForm.description ||
                  quickCargoForm.cargo_items.some(item => !item.cargo_name || !item.weight || !item.price_per_kg)
                }
              >
                Создать груз
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно редактирования профиля */}
      <Dialog open={showEditProfile} onOpenChange={setShowEditProfile}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Редактирование профиля</DialogTitle>
            <DialogDescription>
              Обновите свои личные данные
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="edit_full_name">Полное имя</Label>
              <Input
                id="edit_full_name"
                value={editProfileForm.full_name}
                onChange={(e) => setEditProfileForm({...editProfileForm, full_name: e.target.value})}
                placeholder="Введите полное имя"
              />
            </div>
            <div>
              <Label htmlFor="edit_phone">Телефон</Label>
              <Input
                id="edit_phone"
                value={editProfileForm.phone}
                onChange={(e) => setEditProfileForm({...editProfileForm, phone: e.target.value})}
                placeholder="+7XXXXXXXXXX"
              />
            </div>
            <div>
              <Label htmlFor="edit_email">Email (необязательно)</Label>
              <Input
                id="edit_email"
                type="email"
                value={editProfileForm.email}
                onChange={(e) => setEditProfileForm({...editProfileForm, email: e.target.value})}
                placeholder="example@email.com"
              />
            </div>
            <div>
              <Label htmlFor="edit_address">Адрес (необязательно)</Label>
              <Textarea
                id="edit_address"
                value={editProfileForm.address}
                onChange={(e) => setEditProfileForm({...editProfileForm, address: e.target.value})}
                placeholder="Введите ваш адрес"
                rows={3}
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowEditProfile(false)}>
                Отмена
              </Button>
              <Button onClick={saveProfile}>
                <Save className="mr-2 h-4 w-4" />
                Сохранить
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно повторного заказа */}
      <Dialog open={showRepeatOrderModal} onOpenChange={setShowRepeatOrderModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Повторить заказ</DialogTitle>
            <DialogDescription>
              Создайте новый заказ на основе данных груза #{repeatOrderData?.cargo_number}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6">
            {/* Информация о получателе */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="repeat_recipient_name">Получатель</Label>
                <Input
                  id="repeat_recipient_name"
                  value={repeatOrderForm.recipient_full_name}
                  onChange={(e) => setRepeatOrderForm({...repeatOrderForm, recipient_full_name: e.target.value})}
                  placeholder="ФИО получателя"
                />
              </div>
              <div>
                <Label htmlFor="repeat_recipient_phone">Телефон получателя</Label>
                <Input
                  id="repeat_recipient_phone"
                  value={repeatOrderForm.recipient_phone}
                  onChange={(e) => setRepeatOrderForm({...repeatOrderForm, recipient_phone: e.target.value})}
                  placeholder="+992XXXXXXXXX"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="repeat_recipient_address">Адрес получателя</Label>
              <Textarea
                id="repeat_recipient_address"
                value={repeatOrderForm.recipient_address}
                onChange={(e) => setRepeatOrderForm({...repeatOrderForm, recipient_address: e.target.value})}
                placeholder="Полный адрес доставки"
                rows={2}
              />
            </div>

            {/* Маршрут */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="repeat_route">Маршрут</Label>
                <Select value={repeatOrderForm.route} onValueChange={(value) => setRepeatOrderForm({...repeatOrderForm, route: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="moscow_dushanbe">Москва → Душанбе</SelectItem>
                    <SelectItem value="moscow_khujand">Москва → Худжанд</SelectItem>
                    <SelectItem value="moscow_kulob">Москва → Кулоб</SelectItem>
                    <SelectItem value="moscow_kurgantyube">Москва → Курган-Тюбе</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="repeat_delivery_type">Тип доставки</Label>
                <Select value={repeatOrderForm.delivery_type} onValueChange={(value) => setRepeatOrderForm({...repeatOrderForm, delivery_type: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Стандартная</SelectItem>
                    <SelectItem value="express">Экспресс</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Мульти-груз форма с калькулятором */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium">Грузы для отправки</h3>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addRepeatOrderItem}
                >
                  <Plus className="mr-1 h-4 w-4" />
                  Добавить груз
                </Button>
              </div>

              {/* Список грузов */}
              <div className="space-y-4">
                {repeatOrderForm.cargo_items.map((item, index) => (
                  <div key={index} className="grid grid-cols-12 gap-4 items-end border rounded p-3 bg-gray-50">
                    <div className="col-span-4">
                      <Label>Название груза</Label>
                      <Input
                        value={item.cargo_name}
                        onChange={(e) => handleRepeatOrderItemChange(index, 'cargo_name', e.target.value)}
                        placeholder="Название груза"
                      />
                    </div>
                    <div className="col-span-3">
                      <Label>Вес (кг)</Label>
                      <Input
                        type="number"
                        value={item.weight}
                        onChange={(e) => handleRepeatOrderItemChange(index, 'weight', e.target.value)}
                        placeholder="0.0"
                        step="0.1"
                      />
                    </div>
                    <div className="col-span-3">
                      <Label>Цена за кг (₽)</Label>
                      <Input
                        type="number"
                        value={item.price_per_kg}
                        onChange={(e) => handleRepeatOrderItemChange(index, 'price_per_kg', e.target.value)}
                        placeholder="50"
                        step="0.01"
                      />
                    </div>
                    <div className="col-span-1">
                      <Label className="text-xs text-gray-600">Стоимость</Label>
                      <div className="text-sm font-medium">
                        {((parseFloat(item.weight) || 0) * (parseFloat(item.price_per_kg) || 0)).toFixed(2)} ₽
                      </div>
                    </div>
                    <div className="col-span-1">
                      {repeatOrderForm.cargo_items.length > 1 && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeRepeatOrderItem(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Калькулятор итогов */}
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium mb-3">Расчет стоимости</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {repeatOrderTotalWeight.toFixed(2)} кг
                    </div>
                    <div className="text-sm text-gray-600">Общий вес</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {repeatOrderTotalCost.toFixed(2)} ₽
                    </div>
                    <div className="text-sm text-gray-600">Общая стоимость</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {repeatOrderForm.cargo_items.length}
                    </div>
                    <div className="text-sm text-gray-600">Количество грузов</div>
                  </div>
                </div>

                {/* Детальная разбивка */}
                {repeatOrderBreakdown.length > 0 && (
                  <div className="mt-4">
                    <h5 className="text-sm font-medium mb-2">Детализация по грузам:</h5>
                    <div className="space-y-1">
                      {repeatOrderBreakdown.map((item, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span>{item.cargo_name}: {item.weight}кг × {item.price_per_kg}₽</span>
                          <span className="font-medium">{item.cost.toFixed(2)} ₽</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Дополнительные опции */}
            <div>
              <Label htmlFor="repeat_special_instructions">Особые указания</Label>
              <Textarea
                id="repeat_special_instructions"
                value={repeatOrderForm.special_instructions}
                onChange={(e) => setRepeatOrderForm({...repeatOrderForm, special_instructions: e.target.value})}
                placeholder="Дополнительная информация для доставки"
                rows={2}
              />
            </div>

            {/* Кнопки действий */}
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowRepeatOrderModal(false)}>
                Отмена
              </Button>
              <Button 
                onClick={submitRepeatOrder}
                disabled={
                  !repeatOrderForm.recipient_full_name ||
                  !repeatOrderForm.recipient_phone ||
                  repeatOrderForm.cargo_items.some(item => !item.cargo_name || !item.weight || !item.price_per_kg)
                }
              >
                <ShoppingCart className="mr-2 h-4 w-4" />
                Создать заказ ({repeatOrderTotalCost.toFixed(2)} ₽)
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно редактирования пользователя админом */}
      <Dialog open={showAdminEditUser} onOpenChange={setShowAdminEditUser}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Редактирование пользователя</DialogTitle>
            <DialogDescription>
              Редактирование профиля пользователя: {selectedUserForEdit?.full_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="admin_edit_full_name">Полное имя</Label>
              <Input
                id="admin_edit_full_name"
                value={adminEditUserForm.full_name}
                onChange={(e) => setAdminEditUserForm({...adminEditUserForm, full_name: e.target.value})}
                placeholder="Введите полное имя"
              />
            </div>
            <div>
              <Label htmlFor="admin_edit_phone">Телефон</Label>
              <Input
                id="admin_edit_phone"
                value={adminEditUserForm.phone}
                onChange={(e) => setAdminEditUserForm({...adminEditUserForm, phone: e.target.value})}
                placeholder="+7XXXXXXXXXX"
              />
            </div>
            <div>
              <Label htmlFor="admin_edit_email">Email</Label>
              <Input
                id="admin_edit_email"
                type="email"
                value={adminEditUserForm.email}
                onChange={(e) => setAdminEditUserForm({...adminEditUserForm, email: e.target.value})}
                placeholder="example@email.com"
              />
            </div>
            <div>
              <Label htmlFor="admin_edit_address">Адрес</Label>
              <Textarea
                id="admin_edit_address"
                value={adminEditUserForm.address}
                onChange={(e) => setAdminEditUserForm({...adminEditUserForm, address: e.target.value})}
                placeholder="Введите адрес пользователя"
                rows={3}
              />
            </div>
            <div>
              <Label htmlFor="admin_edit_role">Роль</Label>
              <Select value={adminEditUserForm.role} onValueChange={(value) => setAdminEditUserForm({...adminEditUserForm, role: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Пользователь</SelectItem>
                  <SelectItem value="warehouse_operator">Оператор склада</SelectItem>
                  <SelectItem value="admin">Администратор</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="admin_edit_active"
                checked={adminEditUserForm.is_active}
                onChange={(e) => setAdminEditUserForm({...adminEditUserForm, is_active: e.target.checked})}
              />
              <Label htmlFor="admin_edit_active">Активный пользователь</Label>
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAdminEditUser(false)}>
                Отмена
              </Button>
              <Button onClick={saveAdminUserEdit}>
                <Save className="mr-2 h-4 w-4" />
                Сохранить изменения
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Модальное окно повторного заказа админа/оператора */}
      <Dialog open={showAdminRepeatOrderModal} onOpenChange={setShowAdminRepeatOrderModal}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Повторить заказ (Admin/Operator)</DialogTitle>
            <DialogDescription>
              Создание нового заказа на основе груза #{adminRepeatOrderData?.cargo_number}
              <br />
              <span className="text-xs text-gray-500">
                Данные отправителя и получателя автозаполнены. Заполните данные грузов.
              </span>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6">
            {/* Информация об отправителе (заблокированная) */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-medium mb-3 flex items-center">
                <User className="mr-2 h-5 w-5" />
                Отправитель (автозаполнено)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>ФИО отправителя</Label>
                  <Input
                    value={adminRepeatOrderForm.sender_full_name}
                    onChange={(e) => setAdminRepeatOrderForm({...adminRepeatOrderForm, sender_full_name: e.target.value})}
                    placeholder="ФИО отправителя"
                  />
                </div>
                <div>
                  <Label>Телефон отправителя</Label>
                  <Input
                    value={adminRepeatOrderForm.sender_phone}
                    onChange={(e) => setAdminRepeatOrderForm({...adminRepeatOrderForm, sender_phone: e.target.value})}
                    placeholder="+7XXXXXXXXXX"
                  />
                </div>
              </div>
            </div>

            {/* Информация о получателе (автозаполненная) */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-lg font-medium mb-3 flex items-center">
                <MapPin className="mr-2 h-5 w-5" />
                Получатель (автозаполнено)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>ФИО получателя</Label>
                  <Input
                    value={adminRepeatOrderForm.recipient_full_name}
                    onChange={(e) => setAdminRepeatOrderForm({...adminRepeatOrderForm, recipient_full_name: e.target.value})}
                    placeholder="ФИО получателя"
                  />
                </div>
                <div>
                  <Label>Телефон получателя</Label>
                  <Input
                    value={adminRepeatOrderForm.recipient_phone}
                    onChange={(e) => setAdminRepeatOrderForm({...adminRepeatOrderForm, recipient_phone: e.target.value})}
                    placeholder="+992XXXXXXXXX"
                  />
                </div>
              </div>
              <div className="mt-4">
                <Label>Адрес получателя</Label>
                <Textarea
                  value={adminRepeatOrderForm.recipient_address}
                  onChange={(e) => setAdminRepeatOrderForm({...adminRepeatOrderForm, recipient_address: e.target.value})}
                  placeholder="Полный адрес доставки"
                  rows={2}
                />
              </div>
            </div>

            {/* Маршрут и тип доставки */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Маршрут</Label>
                <Select value={adminRepeatOrderForm.route} onValueChange={(value) => setAdminRepeatOrderForm({...adminRepeatOrderForm, route: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="moscow_dushanbe">Москва → Душанбе</SelectItem>
                    <SelectItem value="moscow_khujand">Москва → Худжанд</SelectItem>
                    <SelectItem value="moscow_kulob">Москва → Кулоб</SelectItem>
                    <SelectItem value="moscow_kurgantyube">Москва → Курган-Тюбе</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Тип доставки</Label>
                <Select value={adminRepeatOrderForm.delivery_type} onValueChange={(value) => setAdminRepeatOrderForm({...adminRepeatOrderForm, delivery_type: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Стандартная</SelectItem>
                    <SelectItem value="express">Экспресс</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Мульти-груз форма с калькулятором для админа */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium flex items-center">
                  <Package className="mr-2 h-5 w-5" />
                  Грузы для отправки (заполните заново)
                </h3>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addAdminRepeatOrderItem}
                >
                  <Plus className="mr-1 h-4 w-4" />
                  Добавить груз
                </Button>
              </div>

              {/* Список грузов */}
              <div className="space-y-4">
                {adminRepeatOrderForm.cargo_items.map((item, index) => (
                  <div key={index} className="grid grid-cols-12 gap-4 items-end border rounded p-3 bg-gray-50">
                    <div className="col-span-4">
                      <Label>Название груза *</Label>
                      <Input
                        value={item.cargo_name}
                        onChange={(e) => handleAdminRepeatOrderItemChange(index, 'cargo_name', e.target.value)}
                        placeholder="Название груза"
                      />
                    </div>
                    <div className="col-span-3">
                      <Label>Вес (кг) *</Label>
                      <Input
                        type="number"
                        value={item.weight}
                        onChange={(e) => handleAdminRepeatOrderItemChange(index, 'weight', e.target.value)}
                        placeholder="0.0"
                        step="0.1"
                      />
                    </div>
                    <div className="col-span-3">
                      <Label>Цена за кг (₽) *</Label>
                      <Input
                        type="number"
                        value={item.price_per_kg}
                        onChange={(e) => handleAdminRepeatOrderItemChange(index, 'price_per_kg', e.target.value)}
                        placeholder="50"
                        step="0.01"
                      />
                    </div>
                    <div className="col-span-1">
                      <Label className="text-xs text-gray-600">Стоимость</Label>
                      <div className="text-sm font-medium">
                        {((parseFloat(item.weight) || 0) * (parseFloat(item.price_per_kg) || 0)).toFixed(2)} ₽
                      </div>
                    </div>
                    <div className="col-span-1">
                      {adminRepeatOrderForm.cargo_items.length > 1 && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeAdminRepeatOrderItem(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Калькулятор итогов для админа */}
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium mb-3 flex items-center">
                  <Calculator className="mr-2 h-4 w-4" />
                  Расчет стоимости
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {adminRepeatOrderTotalWeight.toFixed(2)} кг
                    </div>
                    <div className="text-sm text-gray-600">Общий вес</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {adminRepeatOrderTotalCost.toFixed(2)} ₽
                    </div>
                    <div className="text-sm text-gray-600">Общая стоимость</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {adminRepeatOrderForm.cargo_items.length}
                    </div>
                    <div className="text-sm text-gray-600">Количество грузов</div>
                  </div>
                </div>

                {/* Детальная разбивка */}
                {adminRepeatOrderBreakdown.length > 0 && (
                  <div className="mt-4">
                    <h5 className="text-sm font-medium mb-2">Детализация по грузам:</h5>
                    <div className="space-y-1">
                      {adminRepeatOrderBreakdown.map((item, index) => (
                        <div key={index} className="flex justify-between text-sm">
                          <span>{item.cargo_name || `Груз ${index + 1}`}: {item.weight}кг × {item.price_per_kg}₽</span>
                          <span className="font-medium">{item.cost.toFixed(2)} ₽</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Дополнительные опции */}
            <div>
              <Label>Особые указания</Label>
              <Textarea
                value={adminRepeatOrderForm.special_instructions}
                onChange={(e) => setAdminRepeatOrderForm({...adminRepeatOrderForm, special_instructions: e.target.value})}
                placeholder="Дополнительная информация для доставки"
                rows={2}
              />
            </div>

            {/* Кнопки действий */}
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowAdminRepeatOrderModal(false)}>
                Отмена
              </Button>
              <Button 
                onClick={submitAdminRepeatOrder}
                disabled={
                  !adminRepeatOrderForm.recipient_full_name ||
                  !adminRepeatOrderForm.recipient_phone ||
                  !adminRepeatOrderForm.sender_full_name ||
                  !adminRepeatOrderForm.sender_phone ||
                  adminRepeatOrderForm.cargo_items.some(item => !item.cargo_name || !item.weight || !item.price_per_kg)
                }
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                <ShoppingCart className="mr-2 h-4 w-4" />
                Создать заказ ({adminRepeatOrderTotalCost.toFixed(2)} ₽)
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;