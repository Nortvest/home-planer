const state = {
    currentYear: new Date().getUTCFullYear(),
    currentMonth: new Date().getUTCMonth() + 1,
    users: [],
    calendarTasks: {},
    lastLoadedMonth: null,
};

export function setUsers(users) {
    state.users = [...users];
}

export function getUsers() {
    return [...state.users];
}

export function setCurrentMonth(year, month) {
    state.currentYear = year;
    state.currentMonth = month;
    state.lastLoadedMonth = `${year}-${month}`;
}

export function getCurrentMonth() {
    return { year: state.currentYear, month: state.currentMonth };
}

export function setCalendarTasks(monthKey, tasks) {
    state.calendarTasks[monthKey] = tasks;
}

export function getCalendarTasks(year, month) {
    const key = `${year}-${month}`;
    const tasks = state.calendarTasks[key];
    return tasks ? [...tasks] : null;
}

export function clearCalendarCache() {
    state.calendarTasks = {};
    state.lastLoadedMonth = null;
}
