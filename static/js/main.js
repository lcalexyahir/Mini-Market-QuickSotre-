// Funcionalidades generales

// Auto-cerrar alertas después de 5 segundos
$(document).ready(function() {
    setTimeout(function() {
        $('.alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
    
    // Confirmación para eliminaciones
    $('.delete-confirm').on('click', function(e) {
        if (!confirm('¿Estás seguro de que deseas eliminar este registro? Esta acción no se puede deshacer.')) {
            e.preventDefault();
            return false;
        }
    });
    
    // Búsqueda de clientes (autocomplete)
    if ($('#client-search').length) {
        $('#client-search').autocomplete({
            source: function(request, response) {
                $.ajax({
                    url: '/clients/search',
                    data: { term: request.term },
                    success: function(data) {
                        response($.map(data, function(item) {
                            return {
                                label: item.full_name + ' (' + item.document_id + ')',
                                value: item.full_name,
                                id: item.id
                            };
                        }));
                    }
                });
            },
            minLength: 2,
            select: function(event, ui) {
                $('#client-id').val(ui.item.id);
            }
        });
    }
});

// Función para actualizar estado de asistencia
function updateAttendanceStatus() {
    $.ajax({
        url: '/attendance/api/status',
        method: 'GET',
        success: function(data) {
            if (data.has_checked_in && !data.has_checked_out) {
                $('#check-in-btn').hide();
                $('#check-out-btn').show();
                $('#status-badge').removeClass('bg-secondary').addClass('bg-success').text('Activo');
            } else if (data.has_checked_out) {
                $('#check-in-btn').hide();
                $('#check-out-btn').hide();
                $('#status-badge').removeClass('bg-secondary').addClass('bg-info').text('Completado');
            } else {
                $('#check-in-btn').show();
                $('#check-out-btn').hide();
                $('#status-badge').removeClass('bg-secondary').addClass('bg-warning').text('No registrado');
            }
        }
    });
}

// Actualizar cada 30 segundos si estamos en página de asistencia
if (window.location.pathname.includes('/attendance')) {
    updateAttendanceStatus();
    setInterval(updateAttendanceStatus, 30000);
}