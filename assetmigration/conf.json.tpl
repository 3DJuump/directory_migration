{
    "$schema":"./conf.schema.json",
    "directoryurl" : "https://127.0.0.1/directory",
    "http_username" : "infinite",
    "http_password" : "<password>",
    "infinite_admin_username" : "infinite",
    "infinite_admin_password" : "<password>",
    "asset_file": "path to ndjson of assets in 3.3 version",
    "verifyssl" : true,
    "owner_users": ["<owner user id granted read/write on migrated assets>"],
    "max_chunk_size": "max size of chunks in MB : if omitted, defaults to 256"
}