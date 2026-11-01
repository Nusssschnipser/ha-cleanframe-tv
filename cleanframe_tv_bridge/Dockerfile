FROM mcr.microsoft.com/dotnet/sdk:8.0-bookworm-slim AS launcher
WORKDIR /src
COPY rootfs/app/native-launcher/ ./
RUN dotnet build Launcher.csproj -c Release -o /out --nologo

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY install_sdb.py /tmp/install_sdb.py
RUN python3 /tmp/install_sdb.py && rm /tmp/install_sdb.py && /usr/local/bin/sdb version
WORKDIR /app
COPY rootfs/app/ /app/
COPY --from=launcher /out/Q95Launch.dll /out/Q95Launch.deps.json /out/Q95Launch.runtimeconfig.json /app/native-launcher/out/
COPY run.py /app/run.py
RUN ln -s /data /app/.local
ENV PYTHONUNBUFFERED=1
CMD ["python3", "/app/run.py"]
