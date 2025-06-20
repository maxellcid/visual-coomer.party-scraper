// =========================================================
// static/script.js - Código JavaScript COMPLETO UNIFICADO
// =========================================================

// Elementos de la interfaz principal de descarga
const mainInput = document.getElementById('main_input');
const scrapeForm = document.getElementById('scrapeForm');
const loadingIndicator = document.getElementById('loadingIndicator'); // Spinner principal de descarga
const loadingText = document.getElementById('loadingText'); // Texto de estado de descarga
const submitButton = document.getElementById('submitButton');
const stopButton = document.getElementById('stopButton');
const domainSelect = document.getElementById('domain');
const serviceSelect = document.getElementById('service');
const progressBar = document.getElementById('progressBar');
const progressInfoText = document.getElementById('progressInfoText'); 
const toastContainer = document.getElementById('toastContainer');
const mainInputValidationMessage = document.getElementById('mainInputValidationMessage');
const offsetStartInput = document.getElementById('offset_start');
const offsetStartValidationMessage = document.getElementById('offsetStartValidationMessage');
const offsetEndInput = document.getElementById('offset_end');
const offsetEndValidationMessage = document.getElementById('offsetEndValidationMessage');

// Elementos de la interfaz de búsqueda de creadores (NUEVOS o RENOMBRADOS)
const searchResultsDiv = document.getElementById('results'); // Ahora muestra las tarjetas de creadores
const loadingBarContainerCreators = document.getElementById('loadingBarContainerCreators'); // Barra de carga para lista de creadores
const lastUpdatedCreatorsDiv = document.getElementById('lastUpdatedCreators'); // Última actualización de lista de creadores
const updateButtonCreators = document.getElementById('updateButtonCreators'); // Botón de actualizar lista de creadores
const updateStatusCreatorsSpan = document.getElementById('updateStatusCreators'); // Estado de actualización de lista de creadores

// Elementos de toggles
const toggleOptionsBtn = document.getElementById('toggleOptions');
const advancedOptionsDiv = document.getElementById('advancedOptions');
const themeToggleButton = document.getElementById('themeToggleButton');
const themeToggleIcon = document.getElementById('themeToggleIcon'); 
const toggleOptionsIcon = document.getElementById('toggleOptionsIcon'); 
const languageToggleButton = document.getElementById('languageToggleButton'); 
const currentLanguageText = document.getElementById('currentLanguageText'); 


// Variables de estado
let currentLanguage = 'es'; 
let pollingIntervalId; // Para el proceso de descarga
let currentTaskId = null; // Para el proceso de descarga

// Variables para la lógica de búsqueda de creadores
let creators = []; // Almacena la lista completa de creadores
let debounceTimerSearch; // Para el campo de búsqueda de creadores
const DEBOUNCE_DELAY_SEARCH = 300;
const MAX_RESULTS_TO_DISPLAY = 20; // Máximo de tarjetas a mostrar en la búsqueda

const RETRY_DELAY_ON_503 = 3000;
const MAX_RETRY_ATTEMPTS = 10;
let retryAttempts = 0; // Para la carga de la lista de creadores
const UPDATE_POLLING_INTERVAL_MS_CREATORS = 5000; // Intervalo para el polling de creadores
let updatePollingTimerCreators = null; // Timer para el polling de creadores

const PLACEHOLDER_AVATAR = 'https://via.placeholder.com/100x100?text=No+Img';
const FETCH_TIMEOUT_MS = 30000; // Timeout general para fetches

// --- OBJETO DE TRADUCCIONES ---
// Ampliado para incluir las claves de la app de búsqueda
const translations = {
    en: {
        appName: "Coomer/Kemono Downloader", 
        mainInputLabel: "Creator Username or Full URL:",
        mainInputTooltip: "Enter the creator's username or a full URL (coomer.su/kemono.su).", 
        mainInputPlaceholder: "Ex: user_example or https://coomer.su/onlyfans/user/user_example",
        mainInputValidationInvalid: "Invalid format. Must be a username or a valid URL.",
        startButton: "Start Download", 
        scrapingInProgress: "Download in progress...", 
        stopButton: "Stop Download", 
        showAdvancedOptions: "Show Advanced Options",
        hideAdvancedOptions: "Hide Advanced Options",
        advancedOptionsTitle: "Advanced Options",
        domainLabel: "Domain:",
        domainTooltip: "Domain of the website to download from (coomer.su or kemono.su).",
        serviceLabel: "Service:",
        serviceTooltip: "Platform from which content will be downloaded (e.g. OnlyFans, Patreon).",
        subFoldersCheckbox: "Create subfolders for creators",
        subFoldersTooltip: "Creates a subfolder with the creator's name within the output directory to organize files.",
        skipVidsCheckbox: "Skip videos",
        skipVidsTooltip: "Skips downloading video files to save time and space.",
        skipImgsCheckbox: "Skip images",
        skipImgsTooltip: "Skips downloading image files.",
        fullHashCheckbox: "Calculate full hash (slower, ideal for low bandwidth)",
        fullHashTooltip: "Calculates the hash of downloaded files to verify its integrity. May slow down the process.",
        outputDirLabel: "Download Directory:", 
        outputDirPlaceholder: "Ex: ./downloads", 
        outputDirTooltip: "Specifies the path where all downloaded files will be saved. Default is './files'.", 
        offsetStartLabel: "Start offset:",
        offsetStartPlaceholder: "Ex: 1 (Optional)",
        offsetStartValidationInvalid: "Please enter a valid positive number.",
        offsetEndLabel: "End offset:",
        offsetEndPlaceholder: "Ex: 50 (Optional)",
        offsetEndValidationInvalid: "Please enter a valid positive number.",
        loadingInitial: "Initiating download...", 
        loadingCheckingStatus: "Download in progress. Checking status...", 
        toastErrorFormCorrection: "Please correct the errors in the form before starting the download.", 
        toastErrorConnection: "A server connection error occurred when starting the download.", 
        toastInfoStopRequested: "Request to stop download sent.", 
        toastInfoNoActiveScrape: "No active download process to stop.", 
        toastInfoScrapingCancelled: "Download cancelled by user.", 
        toastErrorUnexpectedResponse: "Unexpected server response.",
        toastErrorStatusCheck: "Error checking download status. Check console for details.", 
        toastErrorInvalidOffsets: "Offsets must be valid numbers.",
        toastErrorUsernameOrUrlRequired: "Please enter a username or a URL.",
        toastErrorInvalidUsername: "Username can only contain letters, numbers, hyphens, underscores, and periods.",
        darkModeButton: "Dark Mode",
        lightModeButton: "Light Mode",
        languageButtonEn: "English",
        languageButtonEs: "Spanish",
        // Nuevos mensajes para el progreso de descarga
        progressDisplay: "Downloaded {downloaded} of {total} files ({percentage}%)",
        progressNoTotal: "Downloaded {downloaded} files...",
        progressInitialStatus: "Initializing download...",
        progressCheckingStatus: "Checking download status...",
        // Nuevos mensajes para el buscador de creadores
        initialSearchMessage: "Preparing creator search...",
        updateCreatorsListButton: "Update List Now",
        creatorsLoadedPrompt: "Creators loaded! Start typing to search.",
        typeToSearch: "Start typing to search for creators.",
        typeAtLeastTwo: "Type at least 2 letters to search.",
        noCreatorsFound: "No creators found for \"{query}\".",
        moreResults: "...and {count} more results. Please be more specific.",
        updatingList: "Requesting list update in background. Search is still active.",
        updatingListWait: "Requesting list update... Please wait.",
        updateInitiated: "Update request sent. Checking status...",
        updatingPleaseWait: "Updating: {message} (Please wait...)",
        updateError: "Polling error: {message}. Check console.",
        connectionErrorUpdate: "Server connection error during check.",
        loadingCreatorsRetry: "Loading creator list (Attempt {attempt}/{max})... please wait.",
        loadingCreatorsTimeout: "Creator list loading timed out. Retrying (Attempt {attempt}/{max})...",
        loadingCreatorsError: "Network or communication error loading creators. Ensure Flask server is running and API is accessible.",
        lastUpdatedStatus: "Last list update: {time} ({status})",
        loadedFromFile: "Loaded {count} creators from file.",
        creatorsLoaded: "Creators loaded!",
        unknown: "Unknown", // Added missing translation key
        pleaseWait: "Please wait...", // Added missing translation key
        unknownError: "Unknown Error", // Added missing translation key
    },
    es: {
        appName: "Coomer/Kemono Downloader", 
        mainInputLabel: "Nombre de Usuario o URL Completa:",
        mainInputTooltip: "Introduce el nombre de usuario del creador o una URL completa (coomer.su/kemono.su).", 
        mainInputPlaceholder: "Ej: usuario_ejemplo o https://coomer.su/onlyfans/user/usuario_de_ejemplo",
        mainInputValidationInvalid: "Formato inválido. Debe ser un nombre de usuario o una URL válida.",
        startButton: "Iniciar Descarga", 
        scrapingInProgress: "Descarga en curso...", 
        stopButton: "Detener Descarga", 
        showAdvancedOptions: "Mostrar Opciones Avanzadas",
        hideAdvancedOptions: "Ocultar Opciones Avanzadas",
        advancedOptionsTitle: "Opciones Avanzadas",
        domainLabel: "Dominio:",
        domainTooltip: "Dominio del sitio web de donde se realizará la descarga (coomer.su o kemono.su).", 
        serviceLabel: "Servicio:",
        serviceTooltip: "Plataforma de la que se descargará el contenido (ej. OnlyFans, Patreon).",
        subFoldersCheckbox: "Crear subcarpetas para creadores",
        subFoldersTooltip: "Crea una subcarpeta con el nombre del creador dentro del directorio de salida para organizar los archivos.",
        skipVidsCheckbox: "Saltar videos",
        skipVidsTooltip: "Omite la descarga de archivos de video para ahorrar tiempo y espacio.",
        skipImgsCheckbox: "Saltar imágenes",
        skipImgsTooltip: "Omite la descarga de archivos de imagen.",
        fullHashCheckbox: "Calcular hash completo (más lento, ideal para bajo ancho de banda)",
        fullHashTooltip: "Calcula el hash de los archivos descargados para verificar su integridad. Puede ralentizar el proceso.",
        outputDirLabel: "Directorio de Descarga:", 
        outputDirPlaceholder: "Ej: ./descargas", 
        outputDirTooltip: "Especifica la ruta donde se guardarán todos los archivos descargados. Por defecto es './files'.", 
        offsetStartLabel: "Offset de inicio:",
        offsetStartPlaceholder: "Ej: 1 (Opcional)",
        offsetStartValidationInvalid: "Por favor, introduce un número positivo válido.",
        offsetEndLabel: "Offset final:",
        offsetEndPlaceholder: "Ej: 50 (Opcional)",
        offsetEndValidationInvalid: "Por favor, introduce un número positivo válido.",
        loadingInitial: "Iniciando descarga...", 
        loadingCheckingStatus: "Descarga en curso. Verificando estado...", 
        toastErrorFormCorrection: "Por favor, corrige los errores en el formulario antes de iniciar la descarga.", 
        toastErrorConnection: "Ocurrió un error de conexión al servidor al iniciar la descarga.", 
        toastInfoStopRequested: "Solicitud para detener la descarga enviada.", 
        toastInfoNoActiveScrape: "No hay ningún proceso de descarga activo para detener.", 
        toastInfoScrapingCancelled: "Descarga cancelada por el usuario.", 
        toastErrorUnexpectedResponse: "Respuesta inesperada del servidor.",
        toastErrorStatusCheck: "Error al verificar el estado de la descarga. Revisa la consola para más detalles.", 
        toastErrorInvalidOffsets: "Los offsets deben ser números válidos.",
        toastErrorUsernameOrUrlRequired: "Por favor, introduce un nombre de usuario o una URL.",
        toastErrorInvalidUsername: "El nombre de usuario solo puede contener letras, números, guiones, guiones bajos y puntos.",
        darkModeButton: "Modo Oscuro",
        lightModeButton: "Modo Claro",
        languageButtonEn: "English",
        languageButtonEs: "Español",
        // Nuevos mensajes para el progreso de descarga
        progressDisplay: "Descargados {downloaded} de {total} archivos ({percentage}%)",
        progressNoTotal: "Descargados {downloaded} archivos...",
        progressInitialStatus: "Iniciando descarga...",
        progressCheckingStatus: "Verificando estado de la descarga...",
        // Nuevos mensajes para el buscador de creadores
        initialSearchMessage: "Preparando el buscador de creadores...",
        updateCreatorsListButton: "Actualizar Lista Ahora",
        creatorsLoadedPrompt: "¡Creadores cargados! Empieza a escribir para buscar.",
        typeToSearch: "Empieza a escribir para buscar creadores.",
        typeAtLeastTwo: "Escribe al menos 2 letras para buscar.",
        noCreatorsFound: "No se encontraron creadores para \"{query}\".",
        moreResults: "...y {count} más resultados. Por favor, sé más específico.",
        updatingList: "Solicitando actualización de la lista en segundo plano. El buscador sigue activo.",
        updatingListWait: "Solicitando actualización de la lista... Por favor, espera.",
        updateInitiated: "Update request sent. Checking status...",
        updatingPleaseWait: "Actualizando: {message} (Por favor, espere...)",
        updateError: "Polling error: {message}. Check console.",
        connectionErrorUpdate: "Server connection error during check.",
        loadingCreatorsRetry: "Cargando la lista de creadores (Intento {attempt}/{max})... por favor, espera.",
        loadingCreatorsTimeout: "Creator list loading timed out. Retrying (Attempt {attempt}/{max})...",
        loadingCreatorsError: "Network or communication error loading creators. Ensure Flask server is running and API is accessible.",
        lastUpdatedStatus: "Last list update: {time} ({status})",
        loadedFromFile: "Cargado {count} creadores desde archivo.",
        creatorsLoaded: "¡Creadores cargados!",
        unknown: "Desconocido", // Added missing translation key
        pleaseWait: "Por favor, espere...", // Added missing translation key
        unknownError: "Error Desconocido", // Added missing translation key
    }
};
// --- FIN OBJETO DE TRADUCCIONES ---

// --- FUNCIÓN PARA ESTABLECER EL IDIOMA DE LA UI ---
function setLanguage(lang) {
    console.log(`[setLanguage] Iniciando con idioma: ${lang}`); // Debug log
    currentLanguage = lang;
    document.documentElement.lang = lang; 
    localStorage.setItem('preferredLanguage', lang); 

    const t = translations[lang];
    console.log(`[setLanguage] Objeto de traducción para ${lang}:`, t); // Debug log

    document.title = t.appName;

    document.querySelectorAll('[data-lang-key]').forEach(element => {
        const key = element.getAttribute('data-lang-key');
        if (t[key]) {
            if (element.tagName === 'INPUT' && element.hasAttribute('placeholder')) {
                element.placeholder = t[key];
            } else if (element.tagName === 'LABEL' && element.hasAttribute('data-tooltip')) {
                element.textContent = t[key];
                const tooltipKey = key.replace('Label', 'Tooltip'); // Convención para tooltips
                if (t[tooltipKey]) {
                    element.setAttribute('data-tooltip', t[tooltipKey]);
                }
            } else {
                element.textContent = t[key];
            }
        }
    });

    // Actualiza placeholders específicos que no se cubren con data-lang-key general
    mainInput.placeholder = t.mainInputPlaceholder;
    offsetStartInput.placeholder = t.offsetStartPlaceholder;
    offsetEndInput.placeholder = t.offsetEndPlaceholder;
    document.getElementById('output_dir').placeholder = t.outputDirPlaceholder;
    
    // Actualizar los tooltips explícitamente si es necesario para labels
    document.querySelector('label[for="main_input"]').setAttribute('data-tooltip', t.mainInputTooltip);
    document.querySelector('label[for="domain"]').setAttribute('data-tooltip', t.domainTooltip);
    document.querySelector('label[for="service"]').setAttribute('data-tooltip', t.serviceTooltip);
    document.querySelector('label[for="sub_folders"]').setAttribute('data-tooltip', t.subFoldersTooltip);
    document.querySelector('label[for="skip_vids"]').setAttribute('data-tooltip', t.skipVidsTooltip);
    document.querySelector('label[for="skip_imgs"]').setAttribute('data-tooltip', t.skipImgsTooltip);
    document.querySelector('label[for="full_hash"]').setAttribute('data-tooltip', t.fullHashTooltip);
    document.querySelector('label[for="output_dir"]').setAttribute('data-tooltip', t.outputDirTooltip); 
    document.querySelector('label[for="offset_start"]').setAttribute('data-tooltip', t.offsetStartTooltip);
    document.querySelector('label[for="offset_end"]').setAttribute('data-tooltip', t.offsetEndTooltip);


    themeToggleButton.querySelector('span').textContent = document.body.classList.contains('dark-mode') ? t.lightModeButton : t.darkModeButton;
    
    // Debug log para currentLanguageText
    console.log(`[setLanguage] Actualizando currentLanguageText con: ${t[`languageButton${lang.charAt(0).toUpperCase() + lang.slice(1)}`]}`);
    currentLanguageText.textContent = t[`languageButton${lang.charAt(0).toUpperCase() + lang.slice(1)}`];

    // Actualiza el texto del botón principal de descarga
    if (submitButton.disabled) {
        submitButton.querySelector('span').textContent = t.scrapingInProgress;
    } else {
        submitButton.querySelector('span').textContent = t.startButton;
    }
    // Actualiza el texto del botón de detener
    stopButton.querySelector('span').textContent = t.stopButton;

    // Actualiza el texto del botón de opciones avanzadas
    const isAdvancedOptionsHidden = window.getComputedStyle(advancedOptionsDiv).display === 'none';
    const optionsSpan = toggleOptionsBtn.querySelector('span');
    const optionsIcon = toggleOptionsBtn.querySelector('i');

    if (isAdvancedOptionsHidden) {
        optionsSpan.textContent = t.showAdvancedOptions;
        optionsIcon.className = "fas fa-cogs"; 
    } else {
        optionsSpan.textContent = t.hideAdvancedOptions;
        optionsIcon.className = "fas fa-cogs"; 
    }

    // Actualiza el texto del botón de actualización de creadores
    // CORRECCIÓN: Accede al span dentro del botón updateButtonCreators
    updateButtonCreators.querySelector('span').textContent = t.updateCreatorsListButton;

    validateNumberInput(offsetStartInput, offsetStartValidationMessage);
    validateNumberInput(offsetEndInput, offsetEndValidationMessage);

    // Vuelve a ejecutar la búsqueda para actualizar los mensajes y tarjetas según el idioma
    searchCreators(); 
    console.log(`[setLanguage] Finalizado para idioma: ${lang}`); // Debug log
}
// --- FIN FUNCIÓN PARA ESTABLECER EL IDIOMA DE LA UI ---

// --- FUNCIONES DE MODO OSCURO ---
function setDarkMode(isDark) {
    if (isDark) {
        document.body.classList.add('dark-mode');
        themeToggleButton.innerHTML = `<i class="fas fa-sun" id="themeToggleIcon"></i> <span data-lang-key="lightModeButton">${translations[currentLanguage].lightModeButton}</span>`;
        localStorage.setItem('theme', 'dark');
    } else {
        document.body.classList.remove('dark-mode');
        themeToggleButton.innerHTML = `<i class="fas fa-moon" id="themeToggleIcon"></i> <span data-lang-key="darkModeButton">${translations[currentLanguage].darkModeButton}</span>`;
        localStorage.setItem('theme', 'light');
    }
}

const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    setDarkMode(true);
} else {
    setDarkMode(false);
}

themeToggleButton.addEventListener('click', () => {
    if (document.body.classList.contains('dark-mode')) {
        setDarkMode(false);
    } else {
        setDarkMode(true);
    }
});
// --- FIN FUNCIONES DE MODO OSCURO ---

// --- FUNCIÓN PARA MOSTRAR NOTIFICACIONES TOAST ---
function showToast(status, messageKey, duration = 5000) {
    const toast = document.createElement('div');
    toast.classList.add('toast', status);

    let iconClass = '';
    if (status === 'success') {
        iconClass = 'fas fa-check-circle';
    } else if (status === 'error') {
        iconClass = 'fas fa-times-circle';
    } else if (status === 'info') {
        iconClass = 'fas fa-info-circle';
    }
    // messageKey puede ser la clave de traducción o el mensaje directo si no es una clave
    const message = translations[currentLanguage][messageKey] || messageKey; 
    toast.innerHTML = `<i class="${iconClass}"></i><span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOutToast 0.5s forwards';
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, duration - 500); 
}
// --- FIN FUNCIÓN TOAST ---

// --- FUNCIÓN PARA RESTRINGIR LA ENTRADA A NÚMEROS ---
function restrictToNumbers(event) {
    const key = event.key;
    if (key >= '0' && key <= '9') {
        return;
    }
    if (['Backspace', 'Tab', 'Delete', 'ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(key)) {
        return;
    }
    event.preventDefault();
}
// --- FIN FUNCIÓN DE RESTRICCIÓN NUMÉRICA ---

// --- FUNCIONES DE VALIDACIÓN EN TIEMPO REAL ---
const urlRegex = /^(https?:\/\/(?:coomer\.su|kemono\.su)\/([^\/]+)\/user\/([^\/]+)(?:\/.*)?)$/i; 
const usernameRegex = /^[a-zA-Z0-9._-]+$/;

function validateMainInput() {
    const value = mainInput.value.trim();
    let isValid = false;

    if (value === "") {
        mainInput.classList.remove('is-valid', 'is-invalid');
        mainInputValidationMessage.style.display = 'none';
        // Cuando el input principal está vacío, se activa la búsqueda general de creadores
        searchCreators();
        return false; 
    }

    const match = value.match(urlRegex);
    if (match) {
        domainSelect.value = match[2]; 
        serviceSelect.value = match[3];
        isValid = true;
    } else if (usernameRegex.test(value)) {
        isValid = true;
    } 
    
    if (isValid) {
        mainInput.classList.remove('is-invalid');
        mainInput.classList.add('is-valid');
        mainInputValidationMessage.style.display = 'none';
        // Si el input es válido como username o URL, triggerear búsqueda de creadores
        searchCreators(); 
    } else {
        mainInput.classList.remove('is-invalid');
        mainInput.classList.add('is-invalid');
        mainInputValidationMessage.textContent = translations[currentLanguage].mainInputValidationInvalid;
        mainInputValidationMessage.style.display = 'block';
        // Si el input no es válido, limpiar los resultados de búsqueda de creadores
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].mainInputValidationInvalid}</p>`;
    }
    return isValid;
}

function validateNumberInput(inputElement, messageElement) {
    const value = inputElement.value.trim();
    if (value === "") {
        inputElement.classList.remove('is-valid', 'is-invalid');
        messageElement.style.display = 'none';
        return true; 
    }

    if (isNaN(value) || parseInt(value) < 0) {
        inputElement.classList.remove('is-valid');
        inputElement.classList.add('is-invalid');
        messageElement.textContent = translations[currentLanguage].offsetStartValidationInvalid; 
        messageElement.style.display = 'block';
        return false;
    } else {
        inputElement.classList.remove('is-invalid');
        inputElement.classList.add('is-valid');
        messageElement.style.display = 'none';
        return true;
    }
}
// --- FIN FUNCIONES DE VALIDACIÓN EN TIEMPO REAL ---

// Función para deshabilitar o habilitar la mayoría de los campos del formulario
function setFormEnabledState(enabled) {
    const inputs = scrapeForm.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.disabled = !enabled;
    });
    submitButton.disabled = !enabled;
    toggleOptionsBtn.classList.remove('disabled'); 
    // Habilitar/deshabilitar los elementos de búsqueda de creadores
    mainInput.disabled = !enabled;
    updateButtonCreators.disabled = !enabled;
}

function showLoading(messageKey = "loadingInitial") {
    loadingIndicator.style.display = 'block';
    loadingText.textContent = translations[currentLanguage][messageKey];
    loadingText.style.display = 'block';
    progressBar.style.display = 'block';
    progressInfoText.style.display = 'block';
    progressBar.value = 0;
    progressBar.max = 1;
    submitButton.disabled = true;
    submitButton.innerHTML = `<i class="fas fa-spinner fa-spin"></i> <span data-lang-key="scrapingInProgress">${translations[currentLanguage].scrapingInProgress}</span>`; 
    stopButton.style.display = 'block'; 
    setFormEnabledState(false);
    // Ocultar elementos de búsqueda de creadores mientras la descarga está activa
    loadingBarContainerCreators.style.display = 'none';
    searchResultsDiv.style.display = 'none';
    lastUpdatedCreatorsDiv.style.display = 'none';
    updateContainerCreators.style.display = 'none';
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
    loadingText.style.display = 'none';
    progressBar.style.display = 'none';
    progressInfoText.style.display = 'none';
    submitButton.disabled = false;
    submitButton.innerHTML = `<i class="fas fa-download"></i> <span data-lang-key="startButton">${translations[currentLanguage].startButton}</span>`; 
    stopButton.style.display = 'none'; 
    setFormEnabledState(true);
    clearInterval(pollingIntervalId);
    currentTaskId = null;
    // Mostrar elementos de búsqueda de creadores de nuevo
    searchResultsDiv.style.display = 'grid'; // O 'block' si no es grid
    lastUpdatedCreatorsDiv.style.display = 'block';
    updateContainerCreators.style.display = 'block';
    // Volver a cargar la lista de creadores después de una descarga si es necesario
    loadCreators(); 
}

function showFinalMessage(status, messageKey) {
    showToast(status, messageKey);
}

toggleOptionsBtn.addEventListener('click', function(e) {
    e.preventDefault(); 
    const isAdvancedOptionsHidden = window.getComputedStyle(advancedOptionsDiv).display === 'none';
    const optionsSpan = this.querySelector('span');
    const optionsIcon = this.querySelector('i');

    if (isAdvancedOptionsHidden) {
        advancedOptionsDiv.style.display = 'block';
        optionsSpan.textContent = translations[currentLanguage].hideAdvancedOptions; 
        optionsIcon.className = "fas fa-cogs"; 
    } else {
        advancedOptionsDiv.style.display = 'none';
        optionsSpan.textContent = translations[currentLanguage].showAdvancedOptions; 
        optionsIcon.className = "fas fa-cogs"; 
    }
});

scrapeForm.addEventListener('submit', function(e) {
    e.preventDefault(); 

    const isMainInputValid = validateMainInput();
    const isOffsetStartValid = validateNumberInput(offsetStartInput, offsetStartValidationMessage);
    const isOffsetEndValid = validateNumberInput(offsetEndInput, offsetEndValidationMessage);

    if (!isMainInputValid || !isOffsetStartValid || !isOffsetEndValid) {
        showFinalMessage('error', 'toastErrorFormCorrection');
        return; 
    }

    const rawInput = mainInput.value.trim(); 
    const urlMatch = rawInput.match(urlRegex);
    
    const processedFormData = new FormData();
    
    if (urlMatch) {
        processedFormData.append('url', urlMatch[0]); 
    } else {
        processedFormData.append('username', rawInput); 
        processedFormData.append('domain', domainSelect.value);
        processedFormData.append('service', serviceSelect.value);
    }

    processedFormData.append('output_dir', document.getElementById('output_dir').value);
    processedFormData.append('sub_folders', document.getElementById('sub_folders').checked ? 'on' : '');
    processedFormData.append('skip_vids', document.getElementById('skip_vids').checked ? 'on' : '');
    processedFormData.append('skip_imgs', document.getElementById('skip_imgs').checked ? 'on' : '');
    processedFormData.append('full_hash', document.getElementById('full_hash').checked ? 'on' : '');
    processedFormData.append('offset_start', document.getElementById('offset_start').value);
    processedFormData.append('offset_end', document.getElementById('offset_end').value);

    showLoading("loadingInitial"); 

    fetch('/scrape', {
        method: 'POST',
        body: processedFormData 
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'processing' && data.task_id) {
            currentTaskId = data.task_id; 
            showLoading("loadingCheckingStatus");
            pollingIntervalId = setInterval(() => {
                checkScrapeStatus(data.task_id);
            }, 3000); 
        } else if (data.status === 'error') {
            hideLoading();
            showFinalMessage('error', data.message); 
        } else {
            hideLoading();
            showFinalMessage('error', 'toastErrorUnexpectedResponse');
        }
    })
    .catch(error => {
        console.error('Error en la solicitud Fetch inicial:', error);
        hideLoading();
        showFinalMessage('error', 'toastErrorConnection');
    });
});

stopButton.addEventListener('click', function() {
    if (currentTaskId) {
        showLoading("toastInfoStopRequested"); 
        fetch(`/stop_scrape/${currentTaskId}`, {
            method: 'POST' 
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showFinalMessage('info', data.message); 
            } else {
                showFinalMessage('error', data.message);
            }
        })
        .catch(error => {
            console.error('Error al intentar detener el scraping:', error);
            showFinalMessage('error', 'Error al intentar detener el scraping.'); 
        });
    } else {
        showFinalMessage('info', 'toastInfoNoActiveScrape');
    }
});

const progressMessageRegex = /Descargando: (\d+) de (\d+) archivos/;

function checkScrapeStatus(taskId) {
    fetch(`/status/${taskId}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'finished') {
            hideLoading();
            showFinalMessage('success', data.message); 
        } else if (data.status === 'error') {
            hideLoading();
            showFinalMessage('error', data.message); 
        } else if (data.status === 'cancelled') {
            hideLoading();
            showFinalMessage('info', 'toastInfoScrapingCancelled'); 
        } 
        else {
            loadingText.textContent = data.message; 

            if (data.progress_info) {
                 const match = data.progress_info.match(progressMessageRegex);
                 if (match) {
                     const downloaded = parseInt(match[1]);
                     const total = parseInt(match[2]);
                     if (!isNaN(downloaded) && !isNaN(total) && total > 0) {
                         progressBar.value = downloaded;
                         progressBar.max = total;
                         const percentage = ((downloaded / total) * 100).toFixed(0);
                         progressInfoText.textContent = translations[currentLanguage].progressDisplay
                             .replace('{downloaded}', downloaded)
                             .replace('{total}', total)
                             .replace('{percentage}', percentage);
                     } else {
                         progressBar.value = downloaded || 0;
                         progressBar.max = 1; 
                         progressInfoText.textContent = translations[currentLanguage].progressNoTotal
                            .replace('{downloaded}', downloaded || 0);
                     }
                 } else {
                     progressBar.value = 0;
                     progressBar.max = 1;
                     progressInfoText.textContent = data.progress_info;
                 }
            } else {
                progressInfoText.style.display = 'none';
                progressBar.value = 0;
                progressBar.max = 1;
            }
        }
    })
    .catch(error => {
        console.error('Error durante el polling del estado:', error);
        hideLoading();
        showFinalMessage('error', 'toastErrorStatusCheck');
    });
}

// =========================================================
// NUEVO: Funciones de Búsqueda de Creadores (del buscador)
// =========================================================

async function loadCreators() {
    console.log("[loadCreators] Iniciado (carga de lista de creadores). Intento actual:", retryAttempts); // Debug log

    loadingBarContainerCreators.style.display = 'block';
    
    // Deshabilitar botones relacionados con la búsqueda mientras se carga la lista
    mainInput.disabled = true;
    updateButtonCreators.disabled = true;

    if (creators.length === 0) {
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].initialSearchMessage}</p>`;
    } else {
        updateStatusCreatorsSpan.textContent = translations[currentLanguage].updatingListWait;
    }
    
    if (retryAttempts > 0) {
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].loadingCreatorsRetry
            .replace('{attempt}', retryAttempts + 1)
            .replace('{max}', MAX_RETRY_ATTEMPTS)}</p`;
    }
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        console.warn(`[loadCreators] Petición a /api/creators excedió el tiempo de espera de ${FETCH_TIMEOUT_MS / 1000}s. Abortando...`); // Debug log
        controller.abort();
    }, FETCH_TIMEOUT_MS);

    try {
        console.log(`[loadCreators] Realizando fetch a /api/creators (Intento ${retryAttempts + 1})...`); // Debug log
        const response = await fetch('/api/creators', { signal: controller.signal }); // Llama al endpoint de tu propio Flask
        clearTimeout(timeoutId); 
        console.log("[loadCreators] Respuesta del fetch obtenida:", response); // Debug log

        if (!response.ok) {
            const errorData = await response.json(); 
            console.error(`[loadCreators] Error de respuesta HTTP: ${response.status} - ${response.statusText}`, errorData); // Debug log

            if (response.status === 503 && retryAttempts < MAX_RETRY_ATTEMPTS) {
                retryAttempts++;
                lastUpdatedCreatorsDiv.textContent = `${translations[currentLanguage].lastUpdatedStatus
                    .replace('{time}', 'N/A')
                    .replace('{status}', errorData.message || translations[currentLanguage].unknownError)}`; // Used unknownError
                console.log(`[loadCreators] Caché no lista (503). Reintentando en ${RETRY_DELAY_ON_503}ms... Intento: ${retryAttempts}`); // Debug log
                setTimeout(loadCreators, RETRY_DELAY_ON_503);
                return; 
            } else {
                searchResultsDiv.innerHTML = `<p class="error-message">${translations[currentLanguage].loadingCreatorsError}</p>`;
                lastUpdatedCreatorsDiv.textContent = `${translations[currentLanguage].lastUpdatedStatus
                    .replace('{time}', 'N/A')
                    .replace('{status}', errorData.message || translations[currentLanguage].unknownError)}`; // Used unknownError
                mainInput.disabled = false; 
                updateButtonCreators.disabled = false;
                loadingBarContainerCreators.style.display = 'none';
            }
        } else {
            const data = await response.json();
            console.log("[loadCreators] Datos JSON recibidos (éxito):", data); // Debug log
            
            creators = data.creators;
            
            const updatedTime = data.last_updated ? new Date(data.last_updated).toLocaleString() : translations[currentLanguage].unknown;
            lastUpdatedCreatorsDiv.textContent = translations[currentLanguage].lastUpdatedStatus
                .replace('{time}', updatedTime)
                .replace('{status}', data.status);

            console.log(`[loadCreators] ¡${creators.length} creadores cargados desde tu servidor local!`); // Debug log
            
            // Si el campo de búsqueda está vacío, o no hay resultados para el query actual
            if (mainInput.value.trim() === '' || searchResultsDiv.innerHTML.includes(translations[currentLanguage].noCreatorsFound.replace('\"{}\"', ''))) {
                 searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].creatorsLoadedPrompt}</p>`;
            }
            searchCreators(); // Vuelve a buscar con el texto actual para mostrar resultados
            
            mainInput.disabled = false;
            updateButtonCreators.disabled = false;
            loadingBarContainerCreators.style.display = 'none';
        }
    } catch (error) {
        clearTimeout(timeoutId); 
        console.error('[loadCreators] ERROR en catch:', error); // Debug log

        if (error.name === 'AbortError' && retryAttempts < MAX_RETRY_ATTEMPTS) {
            console.warn(`[loadCreators] Petición fetch abortada (timeout). Reintentando... Intento: ${retryAttempts + 1}`); // Debug log
            retryAttempts++;
            searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].loadingCreatorsTimeout
                .replace('{attempt}', retryAttempts + 1)
                .replace('{max}', MAX_RETRY_ATTEMPTS)}</p>`;
            lastUpdatedCreatorsDiv.textContent = translations[currentLanguage].loadingCreatorsTimeout
                .replace('{attempt}', retryAttempts + 1)
                .replace('{max}', MAX_RETRY_ATTEMPTS);
            setTimeout(loadCreators, RETRY_DELAY_ON_503); 
            return; 
        } else {
            searchResultsDiv.innerHTML = `<p class="error-message">${translations[currentLanguage].loadingCreatorsError}</p>`;
            lastUpdatedCreatorsDiv.textContent = translations[currentLanguage].loadingCreatorsError;
            mainInput.disabled = true; // Deshabilita el input si hay un error persistente
            updateButtonCreators.disabled = false;
            loadingBarContainerCreators.style.display = 'none';
        }
    } finally {
        if (loadingBarContainerCreators.style.display === 'none' || retryAttempts >= MAX_RETRY_ATTEMPTS) {
             retryAttempts = 0;
             console.log("[loadCreators] Finalizado por éxito o fallo definitivo."); // Debug log
        }
    }
}

function searchCreators() {
    console.log("[searchCreators] Iniciado. Query:", mainInput.value); // Debug log

    const query = mainInput.value.toLowerCase().trim();
    searchResultsDiv.innerHTML = ''; // Limpia resultados anteriores

    if (query.length === 0) {
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].typeToSearch}</p>`;
        return;
    }
    if (query.length < 2) {
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].typeAtLeastTwo}</p>`;
        return;
    }

    const foundCreators = creators.filter(creator =>
        creator.name.toLowerCase().includes(query)
    );
    console.log(`[searchCreators] Creadores encontrados para "${query}": ${foundCreators.length}`); // Debug log

    if (foundCreators.length > 0) {
        const creatorsToDisplay = foundCreators.slice(0, MAX_RESULTS_TO_DISPLAY);

        creatorsToDisplay.forEach(creator => {
            // Construct banner image URL. Assuming it follows the same pattern as avatar but with 'banners'
            const bannerImageUrl = `https://img.coomer.su/banners/${creator.service}/${creator.id}`;
            const creatorPageUrl = `https://coomer.su/${creator.service}/user/${creator.name}`; // URL del creador

            const creatorCardHtml = `
                <a href="${creatorPageUrl}" target="_blank" class="creator-card" style="background-image: url('${bannerImageUrl}'), linear-gradient(to bottom, rgba(0,0,0,0.5), rgba(0,0,0,0.8));">
                    <div class="creator-card-overlay">
                        <div class="creator-left-content">
                            <img src="https://img.coomer.su/icons/${creator.service}/${creator.id}" alt="${creator.name}" onerror="this.onerror=null;this.src='${PLACEHOLDER_AVATAR}';">
                            <div class="creator-text-container">
                                <h3 class="creator-name">${creator.name}</h3>
                                <span class="service-label">${creator.service}</span>
                            </div>
                        </div>
                        <button class="download-button-card" type="button" 
                                data-creator-id="${creator.id}" 
                                data-creator-service="${creator.service}" 
                                data-creator-name="${creator.name}">
                            &#x2193; Descargar
                        </button>
                    </div>
                </a>
            `;
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = creatorCardHtml;
            const creatorCardElement = tempDiv.firstElementChild; // Get the actual card element (which is now an <a>)

            // Event listener for the small download button on the card
            const downloadButtonCard = creatorCardElement.querySelector('.download-button-card');
            downloadButtonCard.addEventListener('click', (event) => {
                event.preventDefault(); // <-- Evita la acción por defecto del enlace padre
                event.stopPropagation(); // Previene que el evento burbujee al enlace padre
                console.log(`[downloadButtonCard] Botón de descarga de tarjeta clicado para ${creator.name}`); // Debug log
                // Rellena el campo principal con el nombre del creador
                mainInput.value = creator.name;
                // También rellena los selects de dominio y servicio
                // Asume coomer.su como dominio por defecto si el servicio está en coomer.su
                domainSelect.value = 'coomer.su'; // La API de Coomer devuelve servicios asociados a coomer.su
                if (['onlyfans', 'patreon', 'fanbox', 'fantia', 'gumroad', 'subscribestar', 'fansly'].includes(creator.service)) {
                    serviceSelect.value = creator.service;
                } else {
                    serviceSelect.value = 'onlyfans'; // Fallback por si acaso
                }
                
                validateMainInput(); // Re-validar y actualizar la UI
                // Opcional: limpiar los resultados de la búsqueda de creadores después de seleccionar uno
                searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].creatorsLoaded}</p>`;
                
                // === NUEVO: Iniciar la descarga automáticamente ===
                submitButton.click(); // Simula un clic en el botón principal de descarga
                // =================================================
            });

            // No se necesita un event listener separado para la tarjeta si es un <a>
            // El comportamiento por defecto del <a> lo maneja
            searchResultsDiv.appendChild(creatorCardElement);
        });

        if (foundCreators.length > MAX_RESULTS_TO_DISPLAY) {
            searchResultsDiv.innerHTML += `<p class="info-message">${translations[currentLanguage].moreResults.replace('{count}', foundCreators.length - MAX_RESULTS_TO_DISPLAY)}</p>`;
        }

    } else {
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].noCreatorsFound.replace('{query}', query)}</p>`;
    }
    console.log("[searchCreators] Finalizado."); // Debug log
}

async function triggerUpdateCreators() {
    console.log("[triggerUpdateCreators] Iniciando actualización manual de la lista de creadores..."); // Debug log
    updateButtonCreators.disabled = true;
    updateStatusCreatorsSpan.textContent = translations[currentLanguage].updatingListWait;
    loadingBarContainerCreators.style.display = 'block';

    if (creators.length > 0) {
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].updatingList}</p>`;
    } else {
        searchResultsDiv.innerHTML = `<p class="info-message">${translations[currentLanguage].updatingListWait}</p>`;
    }

    try {
        // Llama al endpoint de tu propio Flask
        const response = await fetch('/api/update_creators', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            updateStatusCreatorsSpan.textContent = translations[currentLanguage].updateInitiated;
            console.log("[triggerUpdateCreators] Solicitud de actualización enviada. Iniciando polling para verificar estado..."); // Debug log
            startUpdatePollingCreators();
        } else {
            updateStatusCreatorsSpan.textContent = translations[currentLanguage].updateError
                .replace('{message}', data.message || translations[currentLanguage].unknownError);
            updateButtonCreators.disabled = false;
            loadingBarContainerCreators.style.display = 'none';
            if (creators.length === 0) mainInput.disabled = false;
        }
    } catch (error) {
        console.error("[triggerUpdateCreators] Error al solicitar actualización de creadores:", error); // Debug log
        updateStatusCreatorsSpan.textContent = translations[currentLanguage].connectionErrorUpdate;
        updateButtonCreators.disabled = false;
        loadingBarContainerCreators.style.display = 'none';
        if (creators.length === 0) mainInput.disabled = false;
    }
}

function startUpdatePollingCreators() {
    if (updatePollingTimerCreators) {
        clearInterval(updatePollingTimerCreators);
    }

    updatePollingTimerCreators = setInterval(async () => {
        console.log("[startUpdatePollingCreators] Polling: Verificando estado de la caché de creadores..."); // Debug log
        try {
            const response = await fetch('/api/creators'); // Llama al endpoint de tu propio Flask
            const data = await response.json();

            if (response.status === 503) {
                updateStatusCreatorsSpan.textContent = translations[currentLanguage].updatingPleaseWait
                    .replace('{message}', data.message || translations[currentLanguage].pleaseWait);
                loadingBarContainerCreators.style.display = 'block';
                if (creators.length === 0) {
                    mainInput.disabled = true;
                }
            } else if (response.ok) {
                clearInterval(updatePollingTimerCreators);
                updatePollingTimerCreators = null;
                console.log("[startUpdatePollingCreators] Polling: Caché de creadores actualizada detectada. Recargando datos en el frontend."); // Debug log
                retryAttempts = 0; // Resetear intentos de reintento
                loadCreators(); // Recarga la lista de creadores completa
                updateStatusCreatorsSpan.textContent = data.status;
                updateButtonCreators.disabled = false;
            } else {
                console.error("[startUpdatePollingCreators] Polling: Error inesperado en la API de creadores:", data); // Debug log
                clearInterval(updatePollingTimerCreators);
                updatePollingTimerCreators = null;
                updateStatusCreatorsSpan.textContent = translations[currentLanguage].updateError
                    .replace('{message}', data.message || translations[currentLanguage].unknownError);
                updateButtonCreators.disabled = false;
                loadingBarContainerCreators.style.display = 'none';
                if (creators.length === 0) mainInput.disabled = false;
            }
        } catch (error) {
            console.error("[startUpdatePollingCreators] Polling: Error de red o comunicación en la API de creadores:", error); // Debug log
            clearInterval(updatePollingTimerCreators);
            updatePollingTimerCreators = null;
            updateStatusCreatorsSpan.textContent = translations[currentLanguage].connectionErrorUpdate;
            updateButtonCreators.disabled = false;
            loadingBarContainerCreators.style.display = 'none';
            if (creators.length === 0) mainInput.disabled = false;
        }
    }, UPDATE_POLLING_INTERVAL_MS_CREATORS);
}

// =========================================================
// FIN: Funciones de Búsqueda de Creadores
// =========================================================


// --- Event Listeners ---

// El campo main_input ahora dispara la búsqueda de creadores (con debounce)
mainInput.addEventListener('input', () => {
    clearTimeout(debounceTimerSearch);
    debounceTimerSearch = setTimeout(() => {
        validateMainInput(); // Dispara la validación y luego la búsqueda de creadores
    }, DEBOUNCE_DELAY_SEARCH);
});

// Event listeners para validación en tiempo real de offsets
offsetStartInput.addEventListener('input', () => validateNumberInput(offsetStartInput, offsetStartValidationMessage));
offsetEndInput.addEventListener('input', () => validateNumberInput(offsetEndInput, offsetEndValidationMessage));

// Event listener para el botón de actualización de la lista de creadores
updateButtonCreators.addEventListener('click', triggerUpdateCreators);

// DOMContentLoaded para iniciar la carga de la lista de creadores al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    console.log("Script.js cargado. Iniciando carga de creadores.");
    // Asegurarse de que los elementos existan antes de usarlos
    if (!languageToggleButton || !currentLanguageText) {
        console.error("Error: languageToggleButton o currentLanguageText no se encontraron en el DOM.");
        return; // Detener la ejecución si los elementos críticos no están presentes
    }

    // Iniciar la carga de la lista de creadores
    loadCreators(); 
    // Establecer el idioma inicial
    const browserLanguage = navigator.language.split('-')[0];
    const savedLanguage = localStorage.getItem('preferredLanguage');

    if (savedLanguage) {
        currentLanguage = savedLanguage;
    } else if (browserLanguage === 'es') {
        currentLanguage = 'es';
    } else {
        currentLanguage = 'en';
    }
    setLanguage(currentLanguage);

    // Event listener para el botón de cambio de idioma
    languageToggleButton.addEventListener('click', () => {
        console.log("[languageToggleButton] Clic en el botón de idioma detectado."); // Debug log
        const newLanguage = currentLanguage === 'es' ? 'en' : 'es';
        console.log(`[languageToggleButton] Intentando cambiar a idioma: ${newLanguage}`); // Debug log
        setLanguage(newLanguage);
    });
});
