document.addEventListener('DOMContentLoaded', function () {
    const appLabelField = document.getElementById('id_app_label');
    const wrapper = document.querySelector('.form-row.field-milestone_type');

    function fetchMilestoneOptions(app) {
        if (!app) return;
        const initial = window.badgeMilestoneInitial || '';

        fetch(`/admin/accounts/badge/milestone_options/?app=${app}&initial=${encodeURIComponent(initial)}`)
            .then(response => response.json())
            .then(data => {
                if (!data.options) return;

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
            });
    }

    if (appLabelField) {
        appLabelField.addEventListener('change', function () {
            fetchMilestoneOptions(this.value);
        });

        // Trigger once on page load
        if (appLabelField.value) {
            fetchMilestoneOptions(appLabelField.value);
        }
    }
});
