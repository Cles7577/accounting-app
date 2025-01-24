// Modal functions
function openCreateTeamModal() {
    const modal = document.getElementById('createTeamModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeCreateTeamModal() {
    const modal = document.getElementById('createTeamModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function openAddMemberModal(teamId) {
    const modal = document.getElementById('addMemberModal');
    const form = document.getElementById('addMemberForm');
    form.action = `/team/${teamId}/member`;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeAddMemberModal() {
    const modal = document.getElementById('addMemberModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    const addMemberModal = document.getElementById('addMemberModal');
    const createTeamModal = document.getElementById('createTeamModal');
    
    if (event.target === addMemberModal) {
        closeAddMemberModal();
    }
    if (event.target === createTeamModal) {
        closeCreateTeamModal();
    }
});
