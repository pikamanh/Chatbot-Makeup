async function loadConfig() {
    try {
        const response = await fetch('/config.json');
        const config = await response.json();
        return config.NGROK_URL;
    } catch (error) {
        console.error('❌ Error loading config:', error);
        return 'http://localhost:5001'; 
    }
}