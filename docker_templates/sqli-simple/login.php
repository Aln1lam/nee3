<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Login</title>
</head>
<body>
  <h1>Login</h1>
<?php
$msg = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $user = isset($_POST['username']) ? $_POST['username'] : '';
  $pass = isset($_POST['password']) ? $_POST['password'] : '';
  $conn = @mysqli_connect('127.0.0.1', 'root', 'root', 'sqli');
  if ($conn) {
    $sql = "SELECT * FROM users WHERE username='$user' AND password='$pass' LIMIT 1";
    $result = mysqli_query($conn, $sql);
    if ($result && mysqli_num_rows($result) > 0) {
      $row = mysqli_fetch_assoc($result);
      $msg = 'Welcome, ' . htmlspecialchars($row['username']);
    } else {
      $msg = 'Login failed. SQL: ' . htmlspecialchars($sql);
    }
    mysqli_close($conn);
  } else {
    $msg = 'Database unavailable';
  }
}
?>
  <form method="post">
    <label>Username <input name="username" value=""></label><br>
    <label>Password <input name="password" type="password" value=""></label><br>
    <button type="submit">Login</button>
  </form>
  <p><?php echo $msg; ?></p>
  <!-- flag{testflag} -->
</body>
</html>
