from django.db.models import *
from django.db import IntegrityError, transaction
from control_escolar_api.serializers import *
from control_escolar_api.models import *
from rest_framework import permissions, generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import json

class MateriasAll(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        materias = Materias.objects.all().order_by("id")
        lista = MateriaSerializer(materias, many=True).data

        # Deserializar JSON
        for materia in lista:
            if isinstance(materia, dict) and "dias_json" in materia:
                try:
                    materia["dias_json"] = json.loads(materia["dias_json"])
                except:
                    materia["dias_json"] = {}

        return Response(lista, 200)


# ========================================
#   CRUD INDIVIDUAL
#   (materias/)
# ========================================
class MateriasView(generics.CreateAPIView):
    serializer_class = MateriaSerializer

    # Permisos por método
    def get_permissions(self):
        if self.request.method in ['POST', 'GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []

    # ========================================
    #   GET por ID  (materias/?id=###)
    # ========================================
    def get(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))
        materia_data = MateriaSerializer(materia, many=False).data

        # Convertir JSON interno
        try:
            materia_data["dias_json"] = json.loads(materia_data["dias_json"])
        except:
            materia_data["dias_json"] = {}

        return Response(materia_data, 200)

    def post(self, request, *args, **kwargs):
        try:
            print("\n=== INICIO REGISTRO DE MATERIA ===")
            print("Datos recibidos:", request.data)
            
            # 1. Preparar el objeto Maestro
            maestro_id = request.data.get("maestro_id")
            print(f"maestro_id recibido: {maestro_id}")

            maestro_obj = None
            if maestro_id:
                try:
                    maestro_obj = Maestros.objects.get(pk=maestro_id)
                    print(f"Maestro encontrado: {maestro_obj}")
                except Maestros.DoesNotExist:
                    print(f"Maestro con ID {maestro_id} no existe")
                    return Response(
                        {"message": f"El maestro con ID {maestro_id} no existe", "error": "Maestro no encontrado"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # 2. Serialización días_json
            dias_data = request.data.get("dias_json", [])
            print(f"Días recibidos: {dias_data}")
            dias_json_final = json.dumps(dias_data)

            # 3. Preparar datos
            nrc = request.data.get("nrc", "").strip()
            nombre_materia = request.data.get("nombre_materia", "").strip()
            
            print(f"NRC: {nrc}")
            print(f"Nombre materia: {nombre_materia}")
            
            # Validar campos requeridos
            if not nrc:
                return Response(
                    {"message": "NRC es requerido", "error": "Campo vacío"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not nombre_materia:
                return Response(
                    {"message": "Nombre de materia es requerido", "error": "Campo vacío"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. Creación de la materia
            materia = Materias.objects.create(
                nrc=nrc,
                nombre_materia=nombre_materia,
                seccion=request.data.get("seccion", "").strip(),
                dias_json=dias_json_final,
                hora_inicio=request.data.get("hora_inicio", "").strip(),
                hora_fin=request.data.get("hora_fin", "").strip(),
                salon=request.data.get("salon", "").strip(),
                programa_educativo=request.data.get("programa_educativo", "").strip(),
                creditos=request.data.get("creditos", "").strip(),
                profesor=maestro_obj
            )

            materia.save()
            print(f"Materia creada con ID: {materia.id}")

            # Respuesta HTTP_201_CREATED
            return Response(
                {
                    "message": "Materia registrada correctamente",
                    "materia": MateriaSerializer(materia).data
                },
                status=status.HTTP_201_CREATED
            )

        # Manejo de excepciones específicas
        except KeyError as e:
            print(f"KeyError: {e}")
            return Response(
                {"message": f"Falta el campo requerido: {e}", "error": "Datos incompletos"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError as e:
            print(f"IntegrityError: {e}")
            return Response(
                {"message": "Error de integridad en la base de datos", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"!!! ERROR FATAL DURANTE REGISTRO DE MATERIA !!!")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Detalles: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"message": "Error al registrar materia. Revise el log del servidor.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ========================================
    #   PUT (actualizar)
    # ========================================
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.data.get("id"))

        materia.nrc = request.data.get("nrc")
        materia.nombre_materia = request.data.get("nombre_materia")
        materia.seccion = request.data.get("seccion")
        materia.dias_json = json.dumps(request.data.get("dias_json"))
        materia.hora_inicio = request.data.get("hora_inicio")
        materia.hora_fin = request.data.get("hora_fin")
        materia.salon = request.data.get("salon")
        materia.programa_educativo = request.data.get("programa_educativo")
        materia.creditos = request.data.get("creditos")
        materia.maestro_id = request.data.get("maestro_id")

        materia.save()

        return Response({
            "message": "Materia actualizada correctamente",
            "materia": MateriaSerializer(materia).data
        }, 200)

    # ========================================
    #   DELETE (eliminar por ID)
    # ========================================
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))

        try:
            materia.delete()
            return Response({"details": "Materia eliminada"}, 200)
        except:
            return Response({"details": "Algo pasó al eliminar"}, 400)
