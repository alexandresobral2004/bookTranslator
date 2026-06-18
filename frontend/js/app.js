/* ==============================================================================
   BookTranslator - Logic Script (Vanilla JavaScript SPA)
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // DOM Elements Cache
    // -------------------------------------------------------------
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const dropzone = document.getElementById('dropzone');
    const fileInfoBox = document.getElementById('file-info-box');
    const fileNameDisplay = document.getElementById('file-name-display');
    const btnRemoveFile = document.getElementById('btn-remove-file');
    const btnSubmit = document.getElementById('btn-submit');
    
    const useOpenaiCheckbox = document.getElementById('use-openai-checkbox');
    const openaiKeyWrapper = document.getElementById('openai-key-wrapper');
    const openaiKeyInput = document.getElementById('openai-key-input');
    const useGlossaryCheckbox = document.getElementById('use-glossary-checkbox');
    
    const progressPanel = document.getElementById('progress-panel');
    const statusMessage = document.getElementById('status-message');
    const statusPercentage = document.getElementById('status-percentage');
    const progressBarFill = document.getElementById('progress-bar-fill');
    
    const successPanel = document.getElementById('success-panel');
    const btnDownload = document.getElementById('btn-download');

    // Mapeamento de ids das etapas no HTML
    const steps = {
        extracting: document.getElementById('step-extracting'),
        chunking: document.getElementById('step-chunking'),
        translating: document.getElementById('step-translating'),
        postediting: document.getElementById('step-postediting'),
        building: document.getElementById('step-building')
    };

    const stepIcons = {
        extracting: document.getElementById('icon-extracting'),
        chunking: document.getElementById('icon-chunking'),
        translating: document.getElementById('icon-translating'),
        postediting: document.getElementById('icon-postediting'),
        building: document.getElementById('icon-building')
    };

    let selectedFile = null;
    let eventSource = null;
    let currentJobId = null;

    // -------------------------------------------------------------
    // OpenAI Key Toggle Effect
    // -------------------------------------------------------------
    useOpenaiCheckbox.addEventListener('change', () => {
        if (useOpenaiCheckbox.checked) {
            openaiKeyWrapper.classList.add('visible');
        } else {
            openaiKeyWrapper.classList.remove('visible');
            openaiKeyInput.value = ''; // limpa ao desmarcar
        }
    });

    // -------------------------------------------------------------
    // Drag and Drop File Handlers
    // -------------------------------------------------------------
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Apenas arquivos PDF são permitidos!');
            return;
        }

        const maxSizeBytes = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSizeBytes) {
            alert('O arquivo selecionado é muito grande. O limite máximo é 5MB para garantir uma tradução rápida.');
            return;
        }

        selectedFile = file;
        fileNameDisplay.textContent = `${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
        fileInfoBox.style.display = 'flex';
        dropzone.style.display = 'none';
        btnSubmit.disabled = false;
    }

    // Remover arquivo selecionado
    btnRemoveFile.addEventListener('click', (e) => {
        e.stopPropagation();
        resetForm();
    });

    function resetForm() {
        selectedFile = null;
        fileInput.value = '';
        fileInfoBox.style.display = 'none';
        dropzone.style.display = 'block';
        btnSubmit.disabled = true;
    }

    // -------------------------------------------------------------
    // Form Submission & API Request
    // -------------------------------------------------------------
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedFile) return;

        // Desabilita controles do painel de upload
        btnSubmit.disabled = true;
        useGlossaryCheckbox.disabled = true;
        useOpenaiCheckbox.disabled = true;
        openaiKeyInput.disabled = true;
        btnRemoveFile.style.display = 'none';

        // Prepara dados de envio
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('use_glossary', useGlossaryCheckbox.checked);
        formData.append('use_openai_postedit', useOpenaiCheckbox.checked);
        if (openaiKeyInput.value.trim()) {
            formData.append('openai_api_key', openaiKeyInput.value.trim());
        }

        try {
            statusMessage.textContent = 'Enviando PDF para o servidor...';
            statusPercentage.textContent = '0%';
            progressBarFill.style.width = '0%';
            progressPanel.style.display = 'block';

            // Faz upload do arquivo
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Falha ao fazer upload do livro.');
            }

            const data = await response.json();
            currentJobId = data.job_id;
            
            // Oculta o formulário de upload para focar no progresso
            uploadForm.style.display = 'none';
            
            // Inicia escuta SSE em tempo real
            startSSEProgress(currentJobId);

        } catch (err) {
            alert(err.message);
            // Reabilita controles em caso de falha no upload
            btnSubmit.disabled = false;
            useGlossaryCheckbox.disabled = false;
            useOpenaiCheckbox.disabled = false;
            openaiKeyInput.disabled = false;
            btnRemoveFile.style.display = 'block';
            progressPanel.style.display = 'none';
            uploadForm.style.display = 'block';
        }
    });

    // -------------------------------------------------------------
    // SSE Stream Progress Listener
    // -------------------------------------------------------------
    function startSSEProgress(jobId) {
        const url = `/api/status/${jobId}/events`;
        eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const job = JSON.parse(event.data);
                updateProgressUI(job);
            } catch (err) {
                console.error('Erro ao ler evento SSE:', err);
            }
        };

        eventSource.addEventListener('error', (event) => {
            console.error('Erro no stream SSE:', event);
            statusMessage.textContent = 'Erro ao sincronizar progresso com o servidor.';
            statusMessage.style.color = 'var(--error)';
            eventSource.close();
        });
    }

    // -------------------------------------------------------------
    // UI Updates according to Job States
    // -------------------------------------------------------------
    function updateProgressUI(job) {
        // Atualiza barra de progresso global
        const progress = job.progress || 0;
        progressBarFill.style.width = `${progress}%`;
        statusPercentage.textContent = `${Math.round(progress)}%`;
        statusMessage.textContent = job.message;

        // Limpa classes anteriores dos steps
        Object.values(steps).forEach(el => {
            el.className = 'step-item';
        });

        // Configura o status visual das etapas individuais baseando-se no JobStatus
        const status = job.status;
        
        // Etapa 1: Extração
        if (status === 'extracting') {
            setActiveStep('extracting', '⏳');
        } else if (['chunking', 'translating', 'postediting', 'building', 'completed'].includes(status)) {
            setCompletedStep('extracting', '✓');
        }

        // Etapa 2: Chunking
        if (status === 'chunking') {
            setActiveStep('chunking', '⏳');
        } else if (['translating', 'postediting', 'building', 'completed'].includes(status)) {
            setCompletedStep('chunking', '✓');
        }

        // Etapa 3: Tradução
        if (status === 'translating') {
            setActiveStep('translating', '⏳');
        } else if (['postediting', 'building', 'completed'].includes(status)) {
            setCompletedStep('translating', '✓');
        }

        // Etapa 4: Pós-edição (se ativada nas opções)
        if (useOpenaiCheckbox.checked) {
            if (status === 'postediting') {
                setActiveStep('postediting', '⏳');
            } else if (['building', 'completed'].includes(status)) {
                setCompletedStep('postediting', '✓');
            }
        } else {
            // Se desmarcado, pula visualmente
            steps.postediting.style.display = 'none';
        }

        // Etapa 5: Reconstrução PDF
        if (status === 'building') {
            setActiveStep('building', '⏳');
        } else if (status === 'completed') {
            setCompletedStep('building', '✓');
        }

        // Lida com a finalização do job
        if (status === 'completed') {
            eventSource.close();
            setTimeout(() => {
                progressPanel.style.display = 'none';
                successPanel.style.display = 'block';
            }, 800);
        }

        // Lida com falhas
        if (status === 'failed') {
            eventSource.close();
            statusMessage.textContent = `Erro: ${job.error_message || 'Falha no processamento.'}`;
            statusMessage.style.color = 'var(--error)';
            statusPercentage.style.color = 'var(--error)';
            progressBarFill.style.background = 'var(--error)';
        }
    }

    function setActiveStep(stepKey, icon) {
        steps[stepKey].classList.add('active');
        stepIcons[stepKey].textContent = icon;
    }

    function setCompletedStep(stepKey, icon) {
        steps[stepKey].classList.add('completed');
        stepIcons[stepKey].textContent = icon;
    }

    // -------------------------------------------------------------
    // Download Trigger Action
    // -------------------------------------------------------------
    btnDownload.addEventListener('click', () => {
        if (currentJobId) {
            window.location.href = `/api/download/${currentJobId}`;
        }
    });
});
