async function req(url, data) {
  const result = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      credentials: "include",
    },
    body: JSON.stringify(data),
  }).then((resp) => resp.json());
  return result;
}
