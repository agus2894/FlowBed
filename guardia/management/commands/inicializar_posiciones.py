"""
Comando para inicializar las 22 posiciones asistenciales de la guardia.
Uso: python manage.py inicializar_posiciones
"""
from django.core.management.base import BaseCommand
from guardia.models import Posicion


class Command(BaseCommand):
    help = 'Inicializa las 22 posiciones asistenciales de la guardia'

    def handle(self, *args, **options):
        """
        Crea las 22 posiciones:
        - 9 camas (C1-C9)
        - 8 consultorios (CONS1-CONS8)
        - 4 shock rooms (SR1-SR4)
        - 1 aislamiento (ISO1)
        """
        posiciones = []
        
        # 9 camas (C1-C9)
        for i in range(1, 10):
            posiciones.append(Posicion(
                id=f'C{i}',
                tipo='cama',
                estado='LIBRE'
            ))
        
        # 8 consultorios (CONS1-CONS8)
        for i in range(1, 9):
            posiciones.append(Posicion(
                id=f'CONS{i}',
                tipo='consultorio',
                estado='LIBRE'
            ))
        
        # 4 shock rooms (SR1-SR4)
        for i in range(1, 5):
            posiciones.append(Posicion(
                id=f'SR{i}',
                tipo='shock',
                estado='LIBRE'
            ))
        
        # 1 aislamiento (ISO1)
        posiciones.append(Posicion(
            id='ISO1',
            tipo='aislamiento',
            estado='LIBRE'
        ))
        
        # Crear o actualizar las posiciones
        for posicion in posiciones:
            Posicion.objects.update_or_create(
                id=posicion.id,
                defaults={
                    'tipo': posicion.tipo,
                    'estado': posicion.estado,
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Se inicializaron {len(posiciones)} posiciones correctamente')
        )
        self.stdout.write('  - 9 camas (C1-C9)')
        self.stdout.write('  - 8 consultorios (CONS1-CONS8)')
        self.stdout.write('  - 4 shock rooms (SR1-SR4)')
        self.stdout.write('  - 1 aislamiento (ISO1)')
