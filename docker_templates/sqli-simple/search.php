<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Search</title>
</head>
<body>
  <h1>Product Search</h1>
<?php
$id = isset($_GET['id']) ? $_GET['id'] : '1';
$conn = @mysqli_connect('127.0.0.1', 'root', 'root', 'sqli');
if ($conn) {
  $sql = "SELECT id, note FROM secrets WHERE id=$id LIMIT 1";
  $result = mysqli_query($conn, $sql);
  echo '<p>Query: ' . htmlspecialchars($sql) . '</p>';
  if ($result && mysqli_num_rows($result) > 0) {
    while ($row = mysqli_fetch_assoc($result)) {
      echo '<p>Result #' . (int)$row['id'] . ': ' . htmlspecialchars($row['note']) . '</p>';
    }
  } else {
    echo '<p>No result</p>';
  }
  mysqli_close($conn);
} else {
  echo '<p>Database unavailable</p>';
}
?>
  <form method="get">
    <label>ID <input name="id" value="<?php echo htmlspecialchars($id); ?>"></label>
    <button type="submit">Search</button>
  </form>
  <!-- flag{testflag} -->
</body>
</html>
