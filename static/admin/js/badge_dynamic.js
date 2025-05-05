document.addEventListener('DOMContentLoaded', function () {
    const appLabelField = document.getElementById('id_app_label');
    const milestoneFieldWrapper = document.querySelector('.form-row.field-milestone_type');

    function fetchMilestoneOptions(app) {
        if (!app) return;

        const initial = window.badgeMilestoneInitial || '';

        fetch(`/admin/accounts/badge/milestone_options/?app=${app}&initial=${encodeURIComponent(initial)}`)
            .then(response => {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    return response.json();
                } else {
                    return response.text();
                }
            })
            .then(data => {
                const wrapper = document.querySelector('.form-row.field-milestone_type');
                if (!wrapper) return;

                if (typeof data === 'string') {
                    // HTML response for Chores
                    wrapper.innerHTML = data;
                } else if (data.options) {
                    // JSON response for Books
                    const select = document.createElement('select');
                    select.name = 'milestone_type';
                    select.id = 'id_milestone_type';
                    select.required = true;

                    data.options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.id;
                        option.textContent = opt.name;
                        if (opt.id === data.initial) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });

                    wrapper.innerHTML = '';
                    wrapper.appendChild(select);
                }
            });
    }
})
