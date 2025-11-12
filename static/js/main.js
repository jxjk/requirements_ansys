// 通用工具函数
class RequirementsAnalyst {
    static async apiCall(url, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        return await response.json();
    }
    
    static showToast(message, type = 'info') {
        // 简单的 toast 通知实现
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// 看板拖拽功能
if (typeof DragEvent !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        const cards = document.querySelectorAll('.requirement-card');
        
        cards.forEach(card => {
            card.setAttribute('draggable', 'true');
            
            card.addEventListener('dragstart', function(e) {
                e.dataTransfer.setData('text/plain', this.dataset.id);
                this.classList.add('dragging');
            });
            
            card.addEventListener('dragend', function() {
                this.classList.remove('dragging');
            });
        });
        
        const columns = document.querySelectorAll('.status-column');
        
        columns.forEach(column => {
            column.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.classList.add('drag-over');
            });
            
            column.addEventListener('dragleave', function() {
                this.classList.remove('drag-over');
            });
            
            column.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('drag-over');
                
                const requirementId = e.dataTransfer.getData('text/plain');
                const newStatus = this.dataset.status;
                
                // 更新需求状态
                RequirementsAnalyst.apiCall(`/api/requirements/${requirementId}/update`, 'POST', {
                    status: newStatus
                }).then(result => {
                    if (result.success) {
                        RequirementsAnalyst.showToast('需求状态更新成功', 'success');
                        // 可以重新加载页面或更新UI
                        setTimeout(() => location.reload(), 500);
                    }
                });
            });
        });
    });
}
