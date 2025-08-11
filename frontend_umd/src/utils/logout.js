
export const logout = () => {
    localStorage.clear(); // Remove token from storage
    window.location.href = '/login'; // Redirect to login or home page

    // Optionally clear other session data if stored
    //localStorage.removeItem('user');

    // Redirect to login page
    //window.location.href = '/login';
};
