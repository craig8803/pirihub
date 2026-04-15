// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (menuToggle && navMenu) {
        // Toggle menu on button click
        menuToggle.addEventListener('click', function() {
            menuToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking on a link
        const links = navMenu.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', function() {
                menuToggle.classList.remove('active');
                navMenu.classList.remove('active');
                // Close dropdown if open
                document.querySelectorAll('.dropdown.active').forEach(dropdown => {
                    dropdown.classList.remove('active');
                });
            });
        });
        
        // Handle dropdown menus
        const dropdowns = navMenu.querySelectorAll('.dropdown > a');
        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('click', function(e) {
                // On mobile (menu toggle visible), prevent navigation and toggle dropdown instead
                if (menuToggle && menuToggle.offsetParent !== null) {
                    e.preventDefault();
                    const parentDropdown = this.parentElement;
                    parentDropdown.classList.toggle('active');
                }
                // On desktop, let the link navigate normally
            });
        });
    }

    // Lightbox for gallery images
    const overlay = document.createElement('div');
    overlay.id = 'lightbox-overlay';
    const lightboxImg = document.createElement('img');
    overlay.appendChild(lightboxImg);
    document.body.appendChild(overlay);

    function openLightbox(src, alt) {
        lightboxImg.src = src;
        lightboxImg.alt = alt || '';
        overlay.classList.add('active');
    }

    function closeLightbox() {
        overlay.classList.remove('active');
        lightboxImg.src = '';
    }

    overlay.addEventListener('click', closeLightbox);

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeLightbox();
    });

    document.querySelectorAll('.photo-gallery img, .photo-gallery--piri img, .photo-gallery--natural img').forEach(function(img) {
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', function() {
            openLightbox(this.src, this.alt);
        });
    });
});

// Configuration
const API_BASE_URL = 'http://localhost:5001';

// Houses data
const houses = {
    house1: {
        name: "Casa Matutina",
        description: "A charming house in the morning light, perfect for small groups.",
        id: 'casa-matutina'
    },
    house2: {
        name: "Atelier",
        description: "An artistic space for creative minds, with studio areas and inspiration.",
        id: 'atelier'
    },
    house3: {
        name: "Casa Sol",
        description: "Located in a lush valley, ideal for nature lovers.",
        id: 'casa-sol'
    },
    house4: {
        name: "Mini Casa",
        description: "By the river, with access to water activities and relaxation.",
        id: 'mini-casa'
    }
};

let blockedDates = {};

// Function to handle house selection
function selectHouse() {
    const select = document.getElementById('house-select');
    const infoDiv = document.getElementById('house-info');
    const selectedValue = select.value;

    if (selectedValue && houses[selectedValue]) {
        const house = houses[selectedValue];
        infoDiv.innerHTML = `
            <h2>${house.name}</h2>
            <p>${house.description}</p>
        `;
    } else {
        infoDiv.innerHTML = '';
    }
}

// Function to get URL parameter
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// On page load, check for house parameter
window.addEventListener('DOMContentLoaded', function() {
    const houseParam = getUrlParameter('house');
    if (houseParam && document.getElementById('house-select')) {
        const select = document.getElementById('house-select');
        select.value = houseParam;
        selectHouse();
    }

    // Load blocked dates from JSON
    fetch('blocked_dates.json')
        .then(response => response.json())
        .then(data => {
            blockedDates = data;
            renderBookingCalendars();
        })
        .catch(error => {
            console.log('Note: blocked_dates.json not found. Using default.');
            renderBookingCalendars();
        });

    attachReviewFormListeners();
});

// Add event listener if on houses page
if (document.getElementById('house-select')) {
    document.getElementById('house-select').addEventListener('change', selectHouse);
}

function renderBookingCalendars() {
    const calendars = document.querySelectorAll('.booking-calendar');
    if (!calendars.length) {
        return;
    }

    calendars.forEach((calendar) => {
        const viewMode = calendar.dataset.viewMode || 'month';
        
        if (viewMode === 'year') {
            renderYearView(calendar);
        } else {
            renderMonthView(calendar);
        }
    });

    attachCalendarEventListeners();
}

function renderMonthView(calendar) {
    const weekdayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const offset = parseInt(calendar.dataset.monthOffset || '0', 10);
    const today = new Date();
    const baseDate = new Date(today.getFullYear(), today.getMonth() + offset, 1);
    const year = baseDate.getFullYear();
    const month = baseDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDayIndex = firstDay.getDay();
    const totalDays = lastDay.getDate();
    const monthName = firstDay.toLocaleString('default', { month: 'long' });

    // Get house ID for checking blocked dates
    const wrapper = calendar.parentElement;
    let houseId = null;
    if (wrapper && wrapper.querySelector('.booking-button')) {
        const houseName = wrapper.querySelector('.booking-button').dataset.house;
        for (const key in houses) {
            if (houses[key].name === houseName) {
                houseId = houses[key].id;
                break;
            }
        }
    }

    let calendarHtml = '<div class="calendar-header">';
    calendarHtml += '<button class="calendar-nav" data-direction="prev" aria-label="Previous month">&#9664;</button>';
    calendarHtml += '<span class="calendar-title">' + monthName + ' ' + year + '</span>';
    calendarHtml += '<button class="calendar-nav" data-direction="next" aria-label="Next month">&#9654;</button>';
    calendarHtml += '<button class="calendar-view-toggle" data-view="year" aria-label="Year view">Year</button>';
    calendarHtml += '</div>';
    calendarHtml += '<div class="calendar-grid">';

    weekdayLabels.forEach((label) => {
        calendarHtml += '<div class="calendar-cell calendar-weekday">' + label + '</div>';
    });

    for (let i = 0; i < startDayIndex; i += 1) {
        calendarHtml += '<div class="calendar-cell calendar-empty"></div>';
    }

    const selectedStart = calendar.dataset.startDate || '';
    const selectedEnd = calendar.dataset.endDate || '';

    for (let day = 1; day <= totalDays; day += 1) {
        const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        let dayClass = 'calendar-cell calendar-day';

        // Check if date is blocked and from which source
        const blockInfo = getBlockedDateSource(dateString, houseId);
        if (blockInfo.isBlocked) {
            dayClass += ' blocked';
            if (blockInfo.source === 'airbnb') {
                dayClass += ' blocked-airbnb';
            } else if (blockInfo.source === 'booking') {
                dayClass += ' blocked-booking';
            }
        }

        if (selectedStart === dateString) {
            dayClass += ' selected-start';
        }

        if (selectedEnd === dateString) {
            dayClass += ' selected-end';
        }

        if (selectedStart && selectedEnd) {
            const dayDate = new Date(dateString);
            const startDate = new Date(selectedStart);
            const endDate = new Date(selectedEnd);
            if (dayDate > startDate && dayDate < endDate) {
                dayClass += ' selected-range';
            }
        }

        calendarHtml += `<div class="${dayClass}" data-date="${dateString}">${day}</div>`;
    }

    calendarHtml += '</div>';
    calendar.innerHTML = calendarHtml;
}

function renderYearView(calendar) {
    const today = new Date();
    const year = parseInt(calendar.dataset.yearOffset || today.getFullYear());
    
    // Get house ID
    const wrapper = calendar.parentElement;
    let houseId = null;
    if (wrapper && wrapper.querySelector('.booking-button')) {
        const houseName = wrapper.querySelector('.booking-button').dataset.house;
        for (const key in houses) {
            if (houses[key].name === houseName) {
                houseId = houses[key].id;
                break;
            }
        }
    }

    let calendarHtml = '<div class="calendar-header">';
    calendarHtml += '<button class="calendar-nav" data-direction="prev" aria-label="Previous year">&#9664;</button>';
    calendarHtml += '<span class="calendar-title">' + year + '</span>';
    calendarHtml += '<button class="calendar-nav" data-direction="next" aria-label="Next year">&#9654;</button>';
    calendarHtml += '<button class="calendar-view-toggle" data-view="month" aria-label="Month view">Month</button>';
    calendarHtml += '</div>';
    calendarHtml += '<div class="year-grid">';

    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    for (let monthIndex = 0; monthIndex < 12; monthIndex++) {
        const firstDay = new Date(year, monthIndex, 1);
        const lastDay = new Date(year, monthIndex + 1, 0);
        const startDayIndex = firstDay.getDay();
        const totalDays = lastDay.getDate();
        
        calendarHtml += '<div class="year-month">';
        calendarHtml += '<div class="year-month-name">' + monthNames[monthIndex] + '</div>';
        calendarHtml += '<div class="year-month-grid">';
        
        // Add empty cells for offset
        for (let i = 0; i < startDayIndex; i++) {
            calendarHtml += '<div class="year-day empty"></div>';
        }
        
        // Add days
        const selectedStart = calendar.dataset.startDate || '';
        const selectedEnd = calendar.dataset.endDate || '';
        
        for (let day = 1; day <= totalDays; day++) {
            const dateString = `${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            let dayClass = 'year-day';
            
            const blockInfo = getBlockedDateSource(dateString, houseId);
            if (blockInfo.isBlocked) {
                dayClass += ' blocked';
                if (blockInfo.source === 'airbnb') {
                    dayClass += ' blocked-airbnb';
                } else if (blockInfo.source === 'booking') {
                    dayClass += ' blocked-booking';
                }
            }
            
            if (selectedStart === dateString || selectedEnd === dateString) {
                dayClass += ' selected';
            }
            
            if (selectedStart && selectedEnd) {
                const dayDate = new Date(dateString);
                const startDate = new Date(selectedStart);
                const endDate = new Date(selectedEnd);
                if (dayDate > startDate && dayDate < endDate) {
                    dayClass += ' selected-range';
                }
            }
            
            calendarHtml += `<div class="${dayClass}" data-date="${dateString}">${day}</div>`;
        }
        
        calendarHtml += '</div></div>';
    }

    calendarHtml += '</div>';
    calendar.innerHTML = calendarHtml;
}

function attachCalendarEventListeners() {
    const calendars = document.querySelectorAll('.booking-calendar');
    
    calendars.forEach((calendar) => {
        // Get house ID
        const wrapper = calendar.parentElement;
        let houseId = null;
        if (wrapper && wrapper.querySelector('.booking-button')) {
            const houseName = wrapper.querySelector('.booking-button').dataset.house;
            for (const key in houses) {
                if (houses[key].name === houseName) {
                    houseId = houses[key].id;
                    break;
                }
            }
        }

        // Navigation buttons
        calendar.querySelectorAll('.calendar-nav').forEach((button) => {
            button.addEventListener('click', () => {
                const direction = button.dataset.direction;
                const viewMode = calendar.dataset.viewMode || 'month';
                
                if (viewMode === 'year') {
                    const today = new Date();
                    const currentYear = parseInt(calendar.dataset.yearOffset || today.getFullYear());
                    calendar.dataset.yearOffset = direction === 'next' ? currentYear + 1 : currentYear - 1;
                } else {
                    const currentOffset = parseInt(calendar.dataset.monthOffset || '0', 10);
                    calendar.dataset.monthOffset = direction === 'next' ? currentOffset + 1 : currentOffset - 1;
                }
                
                renderBookingCalendars();
            });
        });

        // View toggle button
        const viewToggle = calendar.querySelector('.calendar-view-toggle');
        if (viewToggle) {
            viewToggle.addEventListener('click', () => {
                const newView = viewToggle.dataset.view;
                calendar.dataset.viewMode = newView;
                renderBookingCalendars();
            });
        }

        // Day click handlers
        calendar.querySelectorAll('.calendar-day, .year-day').forEach((cell) => {
            // Prevent interaction with blocked dates
            if (cell.classList.contains('blocked') || cell.classList.contains('empty')) {
                cell.style.pointerEvents = 'none';
                return;
            }

            cell.addEventListener('click', () => {
                const clickedDate = cell.dataset.date;
                const currentStart = calendar.dataset.startDate || '';
                const currentEnd = calendar.dataset.endDate || '';

                if (!currentStart || (currentStart && currentEnd)) {
                    calendar.dataset.startDate = clickedDate;
                    calendar.dataset.endDate = '';
                } else if (currentStart && !currentEnd) {
                    // Validate that the selected range doesn't include blocked dates
                    const startDate = new Date(currentStart);
                    const endDate = new Date(clickedDate);
                    
                    // Ensure start is before end
                    const rangeStart = startDate < endDate ? startDate : endDate;
                    const rangeEnd = startDate < endDate ? endDate : startDate;
                    
                    // Check if any blocked dates fall within this range
                    if (hasBlockedDatesInRange(rangeStart, rangeEnd, houseId)) {
                        alert('Your selected date range includes blocked dates. Please select different dates.');
                        return;
                    }
                    
                    if (new Date(clickedDate) < new Date(currentStart)) {
                        calendar.dataset.startDate = clickedDate;
                    } else {
                        calendar.dataset.endDate = clickedDate;
                    }
                }

                renderBookingCalendars();
            });
        });

        updateBookingSelectionDisplay(calendar);
    });
}

function getBlockedDateSource(dateString, houseId) {
    if (!houseId || !blockedDates[houseId]) {
        return { isBlocked: false, source: null };
    }

    const dateObj = new Date(dateString);
    const ranges = blockedDates[houseId];

    for (const range of ranges) {
        const rangeStart = new Date(range.start);
        const rangeEnd = new Date(range.end);
        if (dateObj >= rangeStart && dateObj < rangeEnd) {
            // Determine source from title
            const source = range.title.toLowerCase().includes('airbnb') ? 'airbnb' : 
                          range.title.toLowerCase().includes('booking') ? 'booking' : null;
            return { isBlocked: true, source: source };
        }
    }

    return { isBlocked: false, source: null };
}

function isDateBlocked(dateString, houseId) {
    return getBlockedDateSource(dateString, houseId).isBlocked;
}

function hasBlockedDatesInRange(startDate, endDate, houseId) {
    if (!houseId || !blockedDates[houseId]) {
        return false;
    }

    const ranges = blockedDates[houseId];
    
    // Check if any blocked date range overlaps with the selected range
    for (const range of ranges) {
        const blockedStart = new Date(range.start);
        const blockedEnd = new Date(range.end);
        
        // Check for any overlap between selected range and blocked range
        // Overlap occurs if: selectedStart < blockedEnd AND selectedEnd > blockedStart
        if (startDate < blockedEnd && endDate > blockedStart) {
            return true;
        }
    }
    
    return false;
}

function updateBookingSelectionDisplay(calendar) {
    const wrapper = calendar.parentElement;
    if (!wrapper) {
        return;
    }

    const startSpan = wrapper.querySelector('.booking-start');
    const endSpan = wrapper.querySelector('.booking-end');
    const nightsSpan = wrapper.querySelector('.booking-nights');
    const bookingButton = wrapper.querySelector('.booking-button');
    const detailsForm = wrapper.querySelector('.booking-details');

    if (!startSpan || !endSpan) {
        return;
    }

    const startDate = calendar.dataset.startDate || '';
    const endDate = calendar.dataset.endDate || '';

    startSpan.textContent = startDate ? new Date(startDate).toLocaleDateString() : 'Not selected';
    endSpan.textContent = endDate ? new Date(endDate).toLocaleDateString() : 'Not selected';

    if (nightsSpan) {
        const nights = startDate && endDate ? calculateNights(startDate, endDate) : 0;
        if (nights > 0 && nights < 14) {
            nightsSpan.innerHTML = `${nights} <span class="min-stay-warning">(Minimum stay is 14 nights)</span>`;
        } else {
            nightsSpan.textContent = String(nights);
        }
    }

    if (bookingButton) {
        const hasRange = Boolean(startDate && endDate);
        const formValues = getBookingFormValues(detailsForm);
        const hasRequiredDetails = formValues.isValid;
        const isEnabled = hasRange && hasRequiredDetails;

        bookingButton.disabled = !isEnabled;
        bookingButton.setAttribute('aria-disabled', String(!isEnabled));

        // Show/hide form based on date selection
        if (detailsForm) {
            if (hasRange) {
                detailsForm.classList.add('visible');
            } else {
                detailsForm.classList.remove('visible');
            }
        }

        if (detailsForm && !detailsForm.dataset.listenerAttached) {
            detailsForm.addEventListener('input', () => {
                updateBookingSelectionDisplay(calendar);
            });
            detailsForm.dataset.listenerAttached = 'true';
        }

        if (!bookingButton.dataset.listenerAttached) {
            bookingButton.addEventListener('click', async () => {
                const currentStart = calendar.dataset.startDate || '';
                const currentEnd = calendar.dataset.endDate || '';
                const currentValues = getBookingFormValues(detailsForm);

                if (!currentStart || !currentEnd || !currentValues.isValid) {
                    return;
                }

                const houseName = bookingButton.dataset.house || 'PiriHub House';
                const nights = calculateNights(currentStart, currentEnd);

                // Find house ID from name
                let houseId = 'casa-matutina';
                for (const [id, house] of Object.entries(houses)) {
                    if (house.name === houseName) {
                        houseId = house.id;
                        break;
                    }
                }

                // Prepare booking data
                const currencyCode = getCurrencyFromCountry(currentValues.countryCode);
                const currencyInfo = getCurrencyInfo(currencyCode);
                
                const bookingData = {
                    firstName: currentValues.firstName,
                    lastName: currentValues.lastName,
                    email: currentValues.email,
                    country: currentValues.countryCode || 'US',
                    countryName: currentValues.countryName || 'United States',
                    phone: currentValues.phone,
                    guests: currentValues.guests,
                    startDate: currentStart,
                    endDate: currentEnd,
                    notes: currentValues.notes,
                    house: houseId,
                    currency: currencyCode,
                    currencyName: currencyInfo.name,
                    currencySymbol: currencyInfo.symbol
                };

                try {
                    bookingButton.disabled = true;
                    bookingButton.textContent = 'Submitting...';

                    const response = await fetch(`${API_BASE_URL}/api/submit-booking`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(bookingData)
                    });

                    const result = await response.json();

                    if (response.ok) {
                        // Show success message
                        alert(`Booking submitted! Booking ID: ${result.bookingId}\n\nYou will receive an email confirmation shortly.`);
                        // Reset form
                        detailsForm.reset();
                        calendar.dataset.startDate = '';
                        calendar.dataset.endDate = '';
                        // Refresh the page to reset UI
                        location.reload();
                    } else {
                        alert(`Error: ${result.error}`);
                        bookingButton.disabled = false;
                        bookingButton.textContent = 'Request Booking';
                    }
                } catch (error) {
                    console.error('Booking submission error:', error);
                    alert('Error submitting booking. Please try again.');
                    bookingButton.disabled = false;
                    bookingButton.textContent = 'Request Booking';
                }
            });
            bookingButton.dataset.listenerAttached = 'true';
        }
    }
}

function getCurrencyFromCountry(countryCode) {
    // Map common country codes to currencies
    const currencyMap = {
        'US': 'USD', 'GB': 'GBP', 'EU': 'EUR', 'CA': 'CAD', 'AU': 'AUD',
        'BR': 'BRL', 'JP': 'JPY', 'CN': 'CNY', 'IN': 'INR', 'MX': 'MXN',
        'CH': 'CHF', 'SE': 'SEK', 'NO': 'NOK', 'DK': 'DKK', 'NZ': 'NZD',
    };
    return currencyMap[countryCode] || 'USD';
}

function getCurrencyInfo(currencyCode) {
    // Map currency codes to names and symbols
    const currencyInfo = {
        'USD': { name: 'US Dollar', symbol: '$' },
        'GBP': { name: 'British Pound', symbol: '£' },
        'EUR': { name: 'Euro', symbol: '€' },
        'CAD': { name: 'Canadian Dollar', symbol: 'C$' },
        'AUD': { name: 'Australian Dollar', symbol: 'A$' },
        'BRL': { name: 'Brazilian Real', symbol: 'R$' },
        'JPY': { name: 'Japanese Yen', symbol: '¥' },
        'CNY': { name: 'Chinese Yuan', symbol: '¥' },
        'INR': { name: 'Indian Rupee', symbol: '₹' },
        'MXN': { name: 'Mexican Peso', symbol: '$' },
        'CHF': { name: 'Swiss Franc', symbol: 'CHF' },
        'SEK': { name: 'Swedish Krona', symbol: 'kr' },
        'NOK': { name: 'Norwegian Krone', symbol: 'kr' },
        'DKK': { name: 'Danish Krone', symbol: 'kr' },
        'NZD': { name: 'New Zealand Dollar', symbol: 'NZ$' },
    };
    return currencyInfo[currencyCode] || { name: currencyCode, symbol: currencyCode };
}

function calculateNights(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = end - start;
    const nights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(nights, 0);
}

function attachReviewFormListeners() {
    const reviewForms = document.querySelectorAll('.review-form');
    reviewForms.forEach((form) => {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const bookingId = form.querySelector('input[name="bookingId"]')?.value.trim() || '';
            const name = form.querySelector('input[name="reviewerName"]').value.trim();
            const rating = form.querySelector('select[name="reviewerRating"]').value;
            const comment = form.querySelector('textarea[name="reviewerComment"]').value.trim();

            if (!bookingId || !name || !rating || !comment) {
                alert('Please fill in all review fields including your booking ID.');
                return;
            }

            // Get house ID from the page
            const houseId = getCurrentHouseId();
            if (!houseId) {
                alert('Unable to determine property. Please try again.');
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/api/submit-review`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        bookingId: bookingId,
                        reviewerName: name,
                        rating: parseInt(rating),
                        comment: comment,
                        house: houseId
                    })
                });

                const result = await response.json();

                if (!response.ok) {
                    alert(`Error: ${result.error || 'Failed to submit review'}`);
                    return;
                }

                alert('Thank you! Your verified review has been submitted successfully.');
                form.reset();
                
                // Reload reviews section to show new review
                loadReviews(houseId);
                
            } catch (error) {
                console.error('Error submitting review:', error);
                alert('Error submitting review. Please try again.');
            }
        });
    });
}

// Helper function to get current house ID from page
function getCurrentHouseId() {
    const h1 = document.querySelector('h1')?.textContent.toLowerCase() || '';
    if (h1.includes('casa matutina')) return 'casa-matutina';
    if (h1.includes('atelier')) return 'atelier';
    if (h1.includes('casa sol')) return 'casa-sol';
    if (h1.includes('mini casa')) return 'mini-casa';
    return null;
}

// Load and display reviews for a house
async function loadReviews(houseId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reviews/${houseId}`);
        
        if (!response.ok) {
            console.error('Failed to load reviews');
            return;
        }
        
        const data = await response.json();
        const reviews = data.reviews || [];
        
        const reviewsSection = document.querySelector('.reviews-section');
        if (!reviewsSection) return;
        
        if (reviews.length === 0) {
            reviewsSection.innerHTML = '<p><em>No reviews yet. Be the first to share your experience!</em></p>';
            return;
        }
        
        let reviewsHtml = '<h3>What our guests say</h3>';
        reviews.forEach(review => {
            const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
            const date = new Date(review.createdAt).toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            const verifiedBadge = review.verified ? ' <span class="verified-badge">✓ Verified Guest</span>' : '';
            
            reviewsHtml += `
                <div class="review">
                    <div class="review-header">
                        <strong>${review.reviewerName}</strong>${verifiedBadge}
                        <div class="review-rating">${stars}</div>
                    </div>
                    <p>"${review.comment}"</p>
                    <p class="review-date"><small>${date}</small></p>
                </div>
            `;
        });
        
        reviewsSection.innerHTML = reviewsHtml;
        
    } catch (error) {
        console.error('Error loading reviews:', error);
    }
}

function getBookingFormValues(detailsForm) {
    if (!detailsForm) {
        return { isValid: false };
    }

    const firstName = detailsForm.querySelector('input[name="firstName"]')?.value.trim() || '';
    const lastName = detailsForm.querySelector('input[name="lastName"]')?.value.trim() || '';
    const emailInput = detailsForm.querySelector('input[name="email"]');
    const email = emailInput?.value.trim() || '';
    const countrySelect = detailsForm.querySelector('select[name="country"]');
    const countryCode = countrySelect?.value || '';
    const countryName = countrySelect?.selectedOptions[0]?.text || '';
    const phoneInput = detailsForm.querySelector('input[name="phone"]');
    const phone = phoneInput?.value.trim() || '';
    const guests = detailsForm.querySelector('input[name="guests"]')?.value.trim() || '';
    const notes = detailsForm.querySelector('textarea[name="notes"]')?.value.trim() || '';

    const emailIsValid = validateEmailFormat(email);
    const emailErrorSpan = detailsForm.querySelector('.email-error');
    
    if (emailInput) {
        emailInput.setCustomValidity(emailIsValid || !email ? '' : 'Please enter a valid email address.');
    }
    
    // Show/hide email error message
    if (emailErrorSpan) {
        if (email && !emailIsValid) {
            emailErrorSpan.style.display = 'block';
        } else {
            emailErrorSpan.style.display = 'none';
        }
    }

    // Validate phone doesn't contain country code
    const phoneIsValid = validatePhoneFormat(phone);
    const phoneErrorSpan = detailsForm.querySelector('.phone-error');
    
    if (phoneInput) {
        phoneInput.setCustomValidity(phoneIsValid || !phone ? '' : 'Please enter phone without country code.');
    }
    
    // Show/hide phone error message
    if (phoneErrorSpan) {
        if (phone && !phoneIsValid) {
            phoneErrorSpan.style.display = 'block';
        } else {
            phoneErrorSpan.style.display = 'none';
        }
    }

    const isValid = Boolean(firstName && lastName && email && countryCode && phone && guests && emailIsValid && phoneIsValid);
    return {
        firstName,
        lastName,
        email,
        countryCode,
        countryName,
        phone,
        fullPhone: countryCode && phone ? `${countryCode} ${phone}` : phone,
        guests,
        notes,
        isValid
    };
}

function validateEmailFormat(email) {
    if (!email) {
        return false;
    }
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhoneFormat(phone) {
    if (!phone) {
        return false;
    }
    // Check if phone starts with + or 00 (country code prefixes)
    if (phone.startsWith('+') || phone.startsWith('00')) {
        return false;
    }
    // Check if phone starts with common country codes (1-3 digits followed by space or non-digit)
    if (/^[0-9]{1,3}[\s\-]/.test(phone)) {
        return false;
    }
    return true;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    renderBookingCalendars();
    attachReviewFormListeners();
    
    // Load reviews for house pages
    const houseId = getCurrentHouseId();
    if (houseId) {
        loadReviews(houseId);
    }
});