window.addEventListener('load', function() {
    console.log('Window loaded');  // Debug log 1
    
    // First verify our elements exist
    const dateDisplay = document.getElementById('date-display');
    const clockDisplay = document.getElementById('clock-display');

    console.log('Date element:', dateDisplay);  // Debug log 2
    console.log('Clock element:', clockDisplay);  // Debug log 3

    if (!dateDisplay || !clockDisplay) {
        console.error('Could not find clock elements!');
        return;
    }

    console.log('Found both elements, setting up clock...');  // Debug log 4

    function updateClock() {
        const now = new Date();
        console.log('Updating clock at:', now);  // Debug log 5
        
        // Update date display
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = days[now.getDay()];
        const dayOfMonth = now.getDate();
        const dateText = `${dayOfWeek}, ${dayOfMonth}`;
        console.log('Setting date to:', dateText);  // Debug log 6
        dateDisplay.textContent = dateText;
        
        // Update clock display
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const timeText = `${hours}:${minutes}:${seconds}`;
        console.log('Setting time to:', timeText);  // Debug log 7
        clockDisplay.textContent = timeText;
    }

    // Update immediately and then every second
    try {
        console.log('Starting clock updates...');  // Debug log 8
        updateClock();
        setInterval(updateClock, 1000);
        console.log('Clock updates started successfully');  // Debug log 9
    } catch (error) {
        console.error('Error starting clock:', error);  // Debug log 10
    }
});
