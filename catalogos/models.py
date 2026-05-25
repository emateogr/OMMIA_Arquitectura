from django.db import models


class Region(models.Model):
    # Catálogo estable para agrupar OOADs y unidades en regiones de reporte.
    region_id = models.CharField(max_length=1, primary_key=True)
    region_name = models.TextField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "region"

    def __str__(self):
        return self.region_name


class Estado(models.Model):
    # Catálogo oficial de entidades federativas; debe alinearse con claves INEGI.
    estado_id = models.CharField(max_length=2, primary_key=True)
    estado_name = models.TextField(unique=True)
    abreviatura = models.CharField(max_length=5, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "estado"

    def __str__(self):
        return self.estado_name


class OOAD(models.Model):
    # Entidad administrativa del IMSS; funciona como agrupador institucional de unidades.
    ooad_id = models.CharField(max_length=2, primary_key=True)
    ooad_name = models.TextField(unique=True)

    # Se guardan llaves, no nombres, para evitar duplicidad e inconsistencias.
    estado = models.ForeignKey(Estado, on_delete=models.RESTRICT, db_column="estado_id", related_name="ooads")
    region = models.ForeignKey(Region, on_delete=models.RESTRICT, db_column="region_id", related_name="ooads")

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ooad"

    def __str__(self):
        return self.ooad_name


class UMAE(models.Model):
    # Entidad de alta especialidad; no equivale necesariamente a una sola clave presupuestal.
    umae_id = models.CharField(max_length=2, primary_key=True)
    umae_name = models.TextField(unique=True)

    # Cada UMAE pertenece a una sola OOAD.
    ooad = models.ForeignKey(OOAD, on_delete=models.RESTRICT, db_column="ooad_id", related_name="umaes")

    # Se almacenan explícitamente para facilitar filtros geográficos y analíticos.
    estado = models.ForeignKey(Estado, on_delete=models.RESTRICT, db_column="estado_id", related_name="umaes")
    region = models.ForeignKey(Region, on_delete=models.RESTRICT, db_column="region_id", related_name="umaes")

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "umae"

    def __str__(self):
        return self.umae_name


class UnidadMedica(models.Model):
    NIVEL_ATENCION_CHOICES = [
        ("0", "Apoyo"),
        ("1", "Primer Nivel"),
        ("2", "Segundo Nivel"),
        ("3", "Tercer Nivel"),
    ]

    # Entidad central de instalaciones; una fila representa una clave presupuestal.
    unidad_id = models.CharField(max_length=12, primary_key=True)
    unidad_name = models.TextField()

    # Asignación administrativa: toda unidad pertenece a una OOAD; la UMAE es opcional.
    ooad = models.ForeignKey(OOAD, on_delete=models.RESTRICT, db_column="ooad_id", related_name="unidades")
    umae = models.ForeignKey(UMAE, on_delete=models.RESTRICT, db_column="umae_id", related_name="unidades", null=True, blank=True)

    # Se guardan directamente para simplificar consultas frecuentes y modelos analíticos.
    estado = models.ForeignKey(Estado, on_delete=models.RESTRICT, db_column="estado_id", related_name="unidades")
    region = models.ForeignKey(Region, on_delete=models.RESTRICT, db_column="region_id", related_name="unidades")

    # Clasificación operativa de la unidad.
    nivel_atencion = models.CharField(max_length=1, choices=NIVEL_ATENCION_CHOICES)
    tipo_unidad = models.TextField()

    # Coordenadas opcionales para análisis espacial y mapas.
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Capacidad instalada: cero es válido, pero el dato no debe faltar.
    consultorios_mf = models.IntegerField(default=0)
    consultorios_mf_umtc = models.IntegerField(default=0)
    consultorios_esp = models.IntegerField(default=0)
    quirofanos = models.IntegerField(default=0)
    camas_censables = models.IntegerField(default=0)
    camas_no_censables = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "unidad_medica"

        # Índices pensados para filtros frecuentes por organización y geografía.
        indexes = [
            models.Index(fields=["ooad"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["region"]),
        ]

        # Reglas mínimas de integridad para evitar capacidades negativas y coordenadas inválidas.
        constraints = [
            models.CheckConstraint(check=models.Q(consultorios_mf__gte=0), name="consultorios_mf_non_negative"),
            models.CheckConstraint(check=models.Q(consultorios_mf_umtc__gte=0), name="consultorios_mf_umtc_non_negative"),
            models.CheckConstraint(check=models.Q(consultorios_esp__gte=0), name="consultorios_esp_non_negative"),
            models.CheckConstraint(check=models.Q(quirofanos__gte=0), name="quirofanos_non_negative"),
            models.CheckConstraint(check=models.Q(camas_censables__gte=0), name="camas_censables_non_negative"),
            models.CheckConstraint(check=models.Q(camas_no_censables__gte=0), name="camas_no_censables_non_negative"),
            models.CheckConstraint(
                check=(models.Q(latitud__gte=-90) & models.Q(latitud__lte=90)) | models.Q(latitud__isnull=True),
                name="latitud_valid_range"
            ),
            models.CheckConstraint(
                check=(models.Q(longitud__gte=-180) & models.Q(longitud__lte=180)) | models.Q(longitud__isnull=True),
                name="longitud_valid_range"
            ),
        ]

    def __str__(self):
        return self.unidad_name