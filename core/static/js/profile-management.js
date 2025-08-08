/**
 * Profile Management JavaScript
 * Handles profile editing, image upload, password changes, and notification settings
 */

class ProfileManager {
    constructor() {
        this.currentUser = null;
        this.uploadedImage = null;
        this.originalFormData = {};
        
        this.init();
    }

    init() {
        console.log('🔧 Initializing Profile Manager...');
        
        // Bind event listeners
        this.bindEventListeners();
        
        // Initialize components
        this.initializeImageUpload();
        this.initializePasswordStrength();
        this.initializeNotificationToggles();
        this.storeOriginalFormData();
        
        console.log('✅ Profile Manager Ready');
    }

    bindEventListeners() {
        // Profile form submission
        const profileForm = document.getElementById('profileForm');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => this.handleProfileSubmit(e));
        }

        // Password form submission
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
        }

        // Cancel button
        const cancelBtn = document.getElementById('cancelProfileBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.handleCancel());
        }

        // Profile picture upload
        const profilePictureInput = document.getElementById('profilePictureInput');
        if (profilePictureInput) {
            profilePictureInput.addEventListener('change', (e) => this.handleImageSelect(e));
        }

        // Upload area click
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('click', () => this.triggerFileInput());
            uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // Remove photo button
        const removePhotoBtn = document.getElementById('removePhotoBtn');
        if (removePhotoBtn) {
            removePhotoBtn.addEventListener('click', () => this.removeProfilePicture());
        }

        // Profile avatar in header click
        const profileAvatarImg = document.getElementById('profileAvatarImg');
        if (profileAvatarImg) {
            profileAvatarImg.addEventListener('click', () => this.triggerFileInput());
        }

        // Password strength checking
        const newPasswordInput = document.getElementById('new_password');
        if (newPasswordInput) {
            newPasswordInput.addEventListener('input', (e) => this.checkPasswordStrength(e.target.value));
        }

        // Password confirmation checking
        const confirmPasswordInput = document.getElementById('confirm_password');
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('blur', () => this.checkPasswordMatch());
        }

        // Toast close button
        const toastClose = document.getElementById('toastClose');
        if (toastClose) {
            toastClose.addEventListener('click', () => this.hideToast());
        }

        // Form change detection
        const formInputs = document.querySelectorAll('#profileForm input, #profileForm select');
        formInputs.forEach(input => {
            input.addEventListener('change', () => this.detectFormChanges());
        });
    }

    initializeImageUpload() {
        // Set up drag and drop
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleImageFile(files[0]);
                }
            });
        }
    }

    initializePasswordStrength() {
        const strengthIndicator = document.getElementById('passwordStrength');
        if (strengthIndicator) {
            // Password strength is handled by input event listener
        }
    }

    initializeNotificationToggles() {
        const toggles = document.querySelectorAll('.notification-settings .toggle-switch');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                toggle.classList.toggle('active');
                this.saveNotificationPreferences();
            });
        });
    }

    storeOriginalFormData() {
        const form = document.getElementById('profileForm');
        if (form) {
            const formData = new FormData(form);
            this.originalFormData = {};
            for (let [key, value] of formData.entries()) {
                this.originalFormData[key] = value;
            }
        }
    }

    detectFormChanges() {
        const form = document.getElementById('profileForm');
        const saveBtn = document.getElementById('saveProfileBtn');
        const cancelBtn = document.getElementById('cancelProfileBtn');
        
        if (!form || !saveBtn || !cancelBtn) return;

        const formData = new FormData(form);
        let hasChanges = false;

        for (let [key, value] of formData.entries()) {
            if (this.originalFormData[key] !== value) {
                hasChanges = true;
                break;
            }
        }

        // Also check if image was uploaded
        if (this.uploadedImage) {
            hasChanges = true;
        }

        // Update button states
        saveBtn.disabled = !hasChanges;
        cancelBtn.style.display = hasChanges ? 'inline-flex' : 'none';
    }

    triggerFileInput() {
        const fileInput = document.getElementById('profilePictureInput');
        if (fileInput) {
            fileInput.click();
        }
    }

    handleImageSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.handleImageFile(file);
        }
    }

    handleImageFile(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            this.showToast('Please select a valid image file', 'error');
            return;
        }

        // Validate file size (5MB max)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            this.showToast('Image size must be less than 5MB', 'error');
            return;
        }

        // Store the uploaded file
        this.uploadedImage = file;

        // Create preview
        const reader = new FileReader();
        reader.onload = (e) => {
            this.updateImagePreview(e.target.result);
        };
        reader.readAsDataURL(file);

        // Detect form changes
        this.detectFormChanges();
    }

    updateImagePreview(imageSrc) {
        // Update preview in upload area
        const previewImage = document.getElementById('previewImage');
        if (previewImage) {
            previewImage.src = imageSrc;
        }

        // Update header avatar
        const profileAvatarImg = document.getElementById('profileAvatarImg');
        if (profileAvatarImg) {
            profileAvatarImg.src = imageSrc;
        }

        // Update user menu avatar if exists
        const userMenuAvatar = document.querySelector('.user-menu-avatar');
        if (userMenuAvatar) {
            userMenuAvatar.src = imageSrc;
        }
    }

    removeProfilePicture() {
        if (confirm('Are you sure you want to remove your profile picture?')) {
            this.uploadedImage = 'remove';
            
            // Reset to default image
            const defaultSrc = '/static/images/default-avatar.png';
            this.updateImagePreview(defaultSrc);
            
            // Clear file input
            const fileInput = document.getElementById('profilePictureInput');
            if (fileInput) {
                fileInput.value = '';
            }

            this.detectFormChanges();
            this.showToast('Profile picture will be removed when you save changes', 'success');
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.currentTarget.classList.remove('dragover');
    }

    handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('dragover');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.handleImageFile(files[0]);
        }
    }

    async handleProfileSubmit(event) {
        event.preventDefault();
        
        const saveBtn = document.getElementById('saveProfileBtn');
        const form = event.target;
        
        // Show loading state
        saveBtn.classList.add('loading');
        saveBtn.disabled = true;

        try {
            // Create form data
            const formData = new FormData(form);
            
            // Add uploaded image if any
            if (this.uploadedImage && this.uploadedImage !== 'remove') {
                formData.append('profile_picture', this.uploadedImage);
            } else if (this.uploadedImage === 'remove') {
                formData.append('remove_picture', 'true');
            }

            // Show upload progress if image is being uploaded
            if (this.uploadedImage && this.uploadedImage !== 'remove') {
                this.showUploadModal();
            }

            // Submit to server
            const response = await fetch('/api/profile/update', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Profile updated successfully!', 'success');
                
                // Update stored form data
                this.storeOriginalFormData();
                this.uploadedImage = null;
                
                // Update page with new data if provided
                if (result.user) {
                    this.updateProfileDisplay(result.user);
                }
                
                // Update user menu if profile picture changed
                if (result.profile_picture_url) {
                    this.updateUserMenuAvatar(result.profile_picture_url);
                }
            } else {
                this.showToast(result.error || 'Failed to update profile', 'error');
            }

        } catch (error) {
            console.error('Profile update error:', error);
            this.showToast('An error occurred while updating your profile', 'error');
        } finally {
            // Hide loading state
            saveBtn.classList.remove('loading');
            saveBtn.disabled = false;
            this.hideUploadModal();
            this.detectFormChanges();
        }
    }

    async handlePasswordSubmit(event) {
        event.preventDefault();
        
        const changeBtn = document.getElementById('changePasswordBtn');
        const form = event.target;
        
        // Validate password match
        if (!this.checkPasswordMatch()) {
            return;
        }

        // Show loading state
        changeBtn.classList.add('loading');
        changeBtn.disabled = true;

        try {
            const formData = new FormData(form);
            
            // Convert to JSON
            const data = {
                current_password: formData.get('current_password'),
                new_password: formData.get('new_password'),
                confirm_password: formData.get('confirm_password')
            };

            const response = await fetch('/api/profile/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Password changed successfully!', 'success');
                form.reset();
                this.resetPasswordStrength();
            } else {
                this.showToast(result.error || 'Failed to change password', 'error');
            }

        } catch (error) {
            console.error('Password change error:', error);
            this.showToast('An error occurred while changing your password', 'error');
        } finally {
            changeBtn.classList.remove('loading');
            changeBtn.disabled = false;
        }
    }

    handleCancel() {
        if (confirm('Are you sure you want to discard your changes?')) {
            // Reset form
            const form = document.getElementById('profileForm');
            if (form) {
                // Reset all form fields to original values
                Object.keys(this.originalFormData).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.value = this.originalFormData[key];
                    }
                });
            }

            // Reset image
            this.uploadedImage = null;
            const originalSrc = document.getElementById('previewImage').dataset.originalSrc || '/static/images/default-avatar.png';
            this.updateImagePreview(originalSrc);

            // Reset file input
            const fileInput = document.getElementById('profilePictureInput');
            if (fileInput) {
                fileInput.value = '';
            }

            this.detectFormChanges();
            this.showToast('Changes discarded', 'success');
        }
    }

    checkPasswordStrength(password) {
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');
        
        if (!strengthFill || !strengthText) return;

        let strength = 0;
        let feedback = '';

        if (password.length === 0) {
            feedback = 'Enter a password';
        } else if (password.length < 6) {
            strength = 1;
            feedback = 'Too short';
        } else {
            // Check various criteria
            if (password.length >= 8) strength++;
            if (/[a-z]/.test(password)) strength++;
            if (/[A-Z]/.test(password)) strength++;
            if (/\d/.test(password)) strength++;
            if (/[^a-zA-Z\d]/.test(password)) strength++;

            switch (strength) {
                case 1:
                case 2:
                    feedback = 'Weak';
                    break;
                case 3:
                    feedback = 'Fair';
                    break;
                case 4:
                    feedback = 'Good';
                    break;
                case 5:
                    feedback = 'Strong';
                    break;
                default:
                    feedback = 'Very weak';
            }
        }

        // Update UI
        strengthFill.className = 'strength-fill';
        if (strength > 0) {
            const strengthLevels = ['', 'weak', 'weak', 'fair', 'good', 'strong'];
            strengthFill.classList.add(strengthLevels[strength]);
        }
        
        strengthText.textContent = feedback;
    }

    checkPasswordMatch() {
        const newPassword = document.getElementById('new_password');
        const confirmPassword = document.getElementById('confirm_password');
        
        if (!newPassword || !confirmPassword) return true;

        const match = newPassword.value === confirmPassword.value;
        
        // Update UI feedback
        if (confirmPassword.value && !match) {
            confirmPassword.setCustomValidity('Passwords do not match');
            this.showToast('Passwords do not match', 'error');
            return false;
        } else {
            confirmPassword.setCustomValidity('');
            return true;
        }
    }

    resetPasswordStrength() {
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');
        
        if (strengthFill) {
            strengthFill.className = 'strength-fill';
        }
        
        if (strengthText) {
            strengthText.textContent = 'Enter a password';
        }
    }

    saveNotificationPreferences() {
        const preferences = {};
        
        // Collect all toggle states
        const toggles = document.querySelectorAll('.notification-settings .toggle-switch');
        toggles.forEach(toggle => {
            const isActive = toggle.classList.contains('active');
            preferences[toggle.id] = isActive;
        });

        // Save to server
        fetch('/api/profile/notification-preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(preferences)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showToast('Notification preferences updated', 'success');
            }
        })
        .catch(error => {
            console.error('Failed to save notification preferences:', error);
        });
    }

    updateProfileDisplay(userData) {
        // Update profile name
        const profileName = document.querySelector('.profile-name');
        if (profileName && userData.username) {
            profileName.textContent = userData.username;
        }

        // Update profile email
        const profileEmail = document.querySelector('.profile-email');
        if (profileEmail && userData.email) {
            profileEmail.textContent = userData.email;
        }

        // Update role
        const profileRole = document.querySelector('.profile-role');
        if (profileRole && userData.role) {
            profileRole.textContent = userData.role.charAt(0).toUpperCase() + userData.role.slice(1);
        }

        // Update user menu name
        const userMenuName = document.querySelector('.user-name');
        if (userMenuName && userData.username) {
            userMenuName.textContent = userData.username;
        }
    }

    updateUserMenuAvatar(avatarUrl) {
        // Update user menu avatar if it exists
        const userMenuAvatar = document.querySelector('.user-menu-avatar');
        if (userMenuAvatar) {
            userMenuAvatar.src = avatarUrl;
        }

        // Update any other avatar instances
        const avatars = document.querySelectorAll('.user-avatar');
        avatars.forEach(avatar => {
            avatar.src = avatarUrl;
        });
    }

    showUploadModal() {
        const modal = document.getElementById('uploadModal');
        if (modal) {
            modal.classList.add('show');
            this.simulateUploadProgress();
        }
    }

    hideUploadModal() {
        const modal = document.getElementById('uploadModal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    simulateUploadProgress() {
        const progressFill = document.getElementById('uploadProgress');
        const progressPercent = document.getElementById('uploadPercent');
        const progressStatus = document.getElementById('uploadStatus');
        
        if (!progressFill || !progressPercent || !progressStatus) return;

        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 100) progress = 100;
            
            progressFill.style.width = progress + '%';
            progressPercent.textContent = Math.round(progress) + '%';
            
            if (progress < 30) {
                progressStatus.textContent = 'Uploading image...';
            } else if (progress < 70) {
                progressStatus.textContent = 'Processing image...';
            } else if (progress < 95) {
                progressStatus.textContent = 'Saving profile...';
            } else {
                progressStatus.textContent = 'Almost done...';
            }
            
            if (progress >= 100) {
                clearInterval(interval);
                setTimeout(() => {
                    this.hideUploadModal();
                }, 500);
            }
        }, 100);
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('notificationToast');
        const toastIcon = document.getElementById('toastIcon');
        const toastMessage = document.getElementById('toastMessage');
        
        if (!toast || !toastIcon || !toastMessage) return;

        // Set icon based on type
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        toastIcon.textContent = icons[type] || icons.info;
        toastMessage.textContent = message;
        
        // Set toast type class
        toast.className = `notification-toast ${type} show`;
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            this.hideToast();
        }, 5000);
    }

    hideToast() {
        const toast = document.getElementById('notificationToast');
        if (toast) {
            toast.classList.remove('show');
        }
    }
}

// Initialize Profile Manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on profile page
    if (document.querySelector('.profile-container')) {
        window.profileManager = new ProfileManager();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProfileManager;
}